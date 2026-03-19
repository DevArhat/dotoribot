import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

import os

from logic import SpaceController

sc = SpaceController()
load_dotenv()
KAKAO_MAP_API_KEY = f"KakaoAK {os.getenv('KAKAO_MAP_API_KEY')}"
REQ_URL = "https://dapi.kakao.com/v2/local/search/keyword.json?"

ITEMS_PER_PAGE = 4
TOTAL_PAGES = 15


class KakaoMapPaginationView(discord.ui.View):
    """카카오맵 검색 결과 페이지네이션 View"""

    def __init__(self, pages, 동네, total_count):
        super().__init__(timeout=None)
        self.pages = pages          # list of list[dict]
        self.동네 = 동네
        self.total_count = total_count
        self.current_page = 0
        self._update_buttons()

    def _update_buttons(self):
        self.first_button.disabled = self.current_page == 0
        self.prev_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page >= len(self.pages) - 1
        self.last_button.disabled = self.current_page >= len(self.pages) - 1
        self.page_indicator.label = f"{self.current_page + 1} / {len(self.pages)}"

    def _build_embed(self):
        page_data = self.pages[self.current_page]
        descriptions = []
        for place in page_data:
            name = place.get('place_name', '이름 없음')
            url = place.get('place_url', '#')
            category = place.get('category_name', '정보 없음')
            address = place.get('road_address_name') or place.get('address_name')
            phone = place.get('phone', '번호 없음')

            item_str = (
                f"### [{name}]({url})\n"
                f"분류 : {category}\n"
                f"위치 : {address}\n"
                f"전화 : {phone}\n"
            )
            descriptions.append(item_str)

        embed = discord.Embed(
            title=f"{self.동네} 검색결과",
            description="\n".join(descriptions),
            color=discord.Color.green()
        )
        embed.set_footer(
            text=f"Powered by Kakao Maps · 총 {self.total_count}개 결과 · 페이지 {self.current_page + 1}/{len(self.pages)}",
            icon_url="https://t1.kakaocdn.net/kakaocorp/corp_nw/logo.png"
        )
        return embed

    @discord.ui.button(label="⏪", style=discord.ButtonStyle.secondary)
    async def first_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = 0
        self._update_buttons()
        await interaction.response.edit_message(embed=self._build_embed(), view=self)

    @discord.ui.button(label="◀", style=discord.ButtonStyle.primary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = max(0, self.current_page - 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self._build_embed(), view=self)

    @discord.ui.button(label="1 / 1", style=discord.ButtonStyle.secondary, disabled=True)
    async def page_indicator(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass  # 페이지 표시용 버튼, 상호작용 없음

    @discord.ui.button(label="▶", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = min(len(self.pages) - 1, self.current_page + 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self._build_embed(), view=self)

    @discord.ui.button(label="⏩", style=discord.ButtonStyle.secondary)
    async def last_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = len(self.pages) - 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self._build_embed(), view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

async def get_kakao_places(keyword: str, max_results: int = 5):
    """카카오 API로 검색어에 대한 상위 장소를 가져옵니다."""
    headers = {"Authorization": KAKAO_MAP_API_KEY}
    params = {"query": keyword, "size": max_results, "sort": "accuracy"}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(REQ_URL, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return data.get('documents', [])
    return []


class PlaceSelect(discord.ui.Select):
    def __init__(self, places, target_type, parent_view_obj):
        self.places = places
        self.target_type = target_type
        self.parent_view_obj = parent_view_obj
        
        options = []
        for i, p in enumerate(places):
            name = p.get('place_name', '이름 없음')
            address = p.get('road_address_name') or p.get('address_name', '주소 없음')
            options.append(discord.SelectOption(
                label=name[:100], 
                description=address[:100], 
                value=str(i)
            ))
            
        super().__init__(placeholder="장소를 선택해주세요...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_idx = int(self.values[0])
        selected_place = self.places[selected_idx]
        
        if self.target_type == "start":
            self.parent_view_obj.start_place = selected_place
        elif self.target_type == "dest":
            self.parent_view_obj.dest_place = selected_place
        elif self.target_type == "waypoint":
            self.parent_view_obj.waypoints.append(selected_place)
            
        # 선택 후 원래 뷰로 메시지를 업데이트합니다.
        await interaction.response.edit_message(embed=self.parent_view_obj.build_embed(), view=self.parent_view_obj)


class PlaceSelectView(discord.ui.View):
    def __init__(self, places, target_type, parent_view_obj):
        super().__init__(timeout=180)
        self.add_item(PlaceSelect(places, target_type, parent_view_obj))
        self.parent_view_obj = parent_view_obj

    @discord.ui.button(label="취소", style=discord.ButtonStyle.danger, row=1)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=self.parent_view_obj.build_embed(), view=self.parent_view_obj)


class SearchModal(discord.ui.Modal):
    def __init__(self, target_type, parent_view_obj):
        title_map = {
            "start": "출발지 검색",
            "dest": "목적지 검색",
            "waypoint": "경유지 검색"
        }
        super().__init__(title=title_map.get(target_type, "장소 검색"))
        self.target_type = target_type
        self.parent_view_obj = parent_view_obj

        self.keyword = discord.ui.TextInput(
            label="검색어",
            placeholder="예: 강남역, 카카오판교아지트 등",
            required=True,
            max_length=50
        )
        self.add_item(self.keyword)

    async def on_submit(self, interaction: discord.Interaction):
        keyword = self.keyword.value
        # thinking=True 없이 defer()를 하면 별도의 알림창 없이 원본 메시지가 수정될 것임을 디스코드에 알립니다.
        await interaction.response.defer()
        
        places = await get_kakao_places(keyword, max_results=5)
        
        if not places:
            await interaction.followup.send("검색 결과가 없습니다.", ephemeral=True)
            return
            
        select_view = PlaceSelectView(places, self.target_type, self.parent_view_obj)
        # 원본 메시지(RoutePlannerView가 있는 메시지)를 업데이트하여 선택 드롭다운으로 교체합니다.
        # 이렇게 하면 지저분한 followup 메시지가 쌓이지 않습니다.
        await interaction.edit_original_response(view=select_view)


class RoutePlannerView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=600)
        self.start_place = None
        self.dest_place = None
        self.waypoints = []

    def build_embed(self):
        embed = discord.Embed(title="🗺️ 경로 계획 🐿️", color=discord.Color.blue())
        
        start_txt = f"{self.start_place['place_name']} ({self.start_place.get('road_address_name') or self.start_place.get('address_name')})" if self.start_place else "미설정"
        embed.add_field(name="🛫 출발지", value=start_txt, inline=False)
        
        if self.waypoints:
            wp_texts = [f"{i+1}. {wp['place_name']}" for i, wp in enumerate(self.waypoints)]
            embed.add_field(name="📍 경유지", value="\n".join(wp_texts), inline=False)
            
        dest_txt = f"{self.dest_place['place_name']} ({self.dest_place.get('road_address_name') or self.dest_place.get('address_name')})" if self.dest_place else "미설정"
        embed.add_field(name="🛬 목적지", value=dest_txt, inline=False)
        
        return embed

    @discord.ui.button(label="출발지 설정", style=discord.ButtonStyle.primary, custom_id="btn_start")
    async def btn_start(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SearchModal("start", self))

    @discord.ui.button(label="목적지 설정", style=discord.ButtonStyle.primary, custom_id="btn_dest")
    async def btn_dest(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SearchModal("dest", self))

    @discord.ui.button(label="경유지 추가", style=discord.ButtonStyle.secondary, custom_id="btn_waypoint")
    async def btn_waypoint(self, interaction: discord.Interaction, button: discord.ui.Button):
        if len(self.waypoints) >= 5:
            await interaction.response.send_message("경유지는 최대 5개까지만 추가할 수 있습니다.", ephemeral=True)
            return
        await interaction.response.send_modal(SearchModal("waypoint", self))

    @discord.ui.button(label="초기화", style=discord.ButtonStyle.danger, custom_id="btn_reset")
    async def btn_reset(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.start_place = None
        self.dest_place = None
        self.waypoints = []
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="완료", style=discord.ButtonStyle.success, custom_id="btn_done")
    async def btn_done(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.start_place or not self.dest_place:
            await interaction.response.send_message("출발지와 목적지를 모두 설정해야 완료할 수 있습니다.", ephemeral=True)
            return
            
        for item in self.children:
            item.disabled = True
            
        embed = self.build_embed()
        embed.color = discord.Color.green()
        embed.set_footer(text="경로 설정 완료!")
        await interaction.response.edit_message(embed=embed, view=self)
        
        # 내부적으로 저장된 결과를 표시합니다.
        msg = f"**[경로 설정 데이터]**\n출발지: {self.start_place['place_name']}\n목적지: {self.dest_place['place_name']}"
        if self.waypoints:
            msg += f"\n경유지: {len(self.waypoints)}곳"
        await interaction.followup.send(content=msg, ephemeral=True)


def _call_kakao_mobility_api(start, dest, waypoints):
    pass



def kakao_map_utils_commands(bot, bot_msg, bot_defer):
    @bot.hybrid_command(name="식당")
    @commands.cooldown(1, 60, commands.BucketType.user)
    @app_commands.describe(
        동네="검색할 동네"
    )
    async def search_kakao_map(ctx, 동네: str = '서울'):
        search_key = sc.remove_space(동네)
        await bot_defer(ctx, defer_msg=f"🐿️ {동네.strip()} 돌아다녀보고 올게요!")
        headers = {
            "Authorization": KAKAO_MAP_API_KEY
        }

        # 카카오 API에서 최대 size=15, page 1~4 로 최대 60개 결과를 가져옴
        # 그 중 ITEMS_PER_PAGE * TOTAL_PAGES = 60개까지 사용
        all_documents = []
        max_needed = ITEMS_PER_PAGE * TOTAL_PAGES  # 60

        for page_num in range(1, 5):  # page 1, 2, 3, 4
            if len(all_documents) >= max_needed:
                break

            params = {
                "query": f"{search_key}",
                "category_group_code": "FD6",
                "sort": "accuracy",
                "size": 15,
                "page": page_num
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(REQ_URL, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        documents = data.get('documents', [])
                        all_documents.extend(documents)

                        # API가 마지막 페이지인지 확인
                        meta = data.get('meta', {})
                        if meta.get('is_end', True):
                            break
                    else:
                        if not all_documents:
                            bot.add_log(ctx, "/식당", f"{동네}, 응답:{response.status}")
                            return await bot_msg(ctx, "😉 못찾았어!")
                        break

        if not all_documents:
            bot.add_log(ctx, "/식당", f"{동네}, 결과없음")
            return await bot_msg(ctx, "😉 못찾았어!")

        # max_needed 개까지만 사용
        all_documents = all_documents[:max_needed]

        # ITEMS_PER_PAGE 단위로 페이지 분할
        pages = []
        for i in range(0, len(all_documents), ITEMS_PER_PAGE):
            pages.append(all_documents[i:i + ITEMS_PER_PAGE])

        total_count = len(all_documents)

        view = KakaoMapPaginationView(pages, 동네, total_count)
        embed = view._build_embed()

        bot.add_log(ctx, "/식당", f"{동네}, {total_count}개 결과, {len(pages)}페이지")

        # interaction 기반으로 view 전송
        inter = ctx if isinstance(ctx, discord.Interaction) else getattr(ctx, 'interaction', None)
        if inter:
            await inter.edit_original_response(content="# 밥먹자 :yum:", embed=embed, view=view)
        else:
            await ctx.send(content="# 밥먹자 :yum:", embed=embed, view=view)

    @search_kakao_map.error
    async def kakao_map_error(ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            # 쿨타임 중일 때 bot_msg 호출
            await bot_msg(ctx, content=f"🤫 아직 식당을 찾을 수 없어요! {error.retry_after:.1f}초 후에 다시 시도해주세요.", ephemeral=True)
        else:
            # 기타 에러는 상위 핸들러가 처리하도록 다시 발생
            raise error

    @bot.hybrid_command(name="경로")
    async def route_planner(ctx):
        """출발지, 경유지, 목적지를 설정하는 대화형 패널을 엽니다."""
        view = RoutePlannerView()
        await ctx.send(embed=view.build_embed(), view=view, ephemeral=True)
