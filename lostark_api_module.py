import discord
from dotenv import load_dotenv

import os
from collections import Counter

import const
from logic import SpaceController


load_dotenv()
sc = SpaceController()

LOSTARK_API_KEY = os.getenv('LOSTARK_API_KEY')

class Lostark_Api:
    def __init__(self, session):
        self.session = session
        self.base_url = "https://developer-lostark.game.onstove.com"
        self.headers = {
            'accept': 'application/json',
            'authorization': f'bearer {LOSTARK_API_KEY}'
        }

    async def get_info(self, char_name: str):
        url = f"{self.base_url}/armories/characters/{char_name}"

        async with self.session.get(url, headers = self.headers) as response:
            if response.status == 200:
                return await response.json()
            elif response.status == 404:
                return "캐릭터를 못찾았어! 😱"
            else:
                return f"API 호출 오류: {response.status}"
    
    async def get_siblings(self, char_name: str):
        url = f"{self.base_url}/characters/{char_name}/siblings"

        async with self.session.get(url, headers = self.headers) as response:
            if response.status == 200:
                return await response.json()
            elif response.status == 404:
                return "캐릭터를 못찾았어! 😱"
            else:
                return f"API 호출 오류: {response.status}"



def parse_character(data: dict) -> dict:
    """
    로스트아크 API response.json() 을 받아 필요한 필드만 추출한 dict 반환.

    Parameters
    ----------
    data : dict
        response.json() 결과 (API 원본 dict)

    Returns
    -------
    dict
        {
            char_img_url, char_name, class, server
            crit, spec, swift,
            combat_pwr, item_lvl,
            engravings, ability_stone,
            gems,
            arkp_title,
            arkg_cores,
        }
    """
    result = {}

    # ── ArmoryProfile ──────────────────────────────────────────────────────
    profile = data.get("ArmoryProfile") or {}

    # 캐릭터 이미지 URL
    result["char_img_url"] = profile.get("CharacterImage")

    # 캐릭터 기본정보 str
    result["char_name"] = profile.get("CharacterName")
    result["class"] = profile.get("CharacterClassName")
    result["server"] = profile.get("ServerName")

    # 전투 특성 (치명 / 특화 / 신속)
    stat_map = {"치명": "crit", "특화": "spec", "신속": "swift"}
    for stat in profile.get("Stats") or []:
        key = stat_map.get(stat.get("Type"))
        if key:
            result[key] = int(stat["Value"])

    # 결과 dict에 키가 없는 경우 None 으로 채움
    for k in stat_map.values():
        result.setdefault(k, None)

    # 전투력 / 아이템 평균 레벨 (문자열 그대로 보존)
    result["combat_pwr"] = profile.get("CombatPower")
    result["item_lvl"] = profile.get("ItemAvgLevel")

    # ── ArmoryEngraving ────────────────────────────────────────────────────
    engraving_section = data.get("ArmoryEngraving") or {}
    effects = engraving_section.get("ArkPassiveEffects") or []

    normal_parts = []   # AbilityStoneLevel is None  →  engravings
    stone_parts  = []   # AbilityStoneLevel not None →  ability_stone
    temp_stone = {}
    stone_level_dict = {
        1: 6,
        2: 7,
        3: 9,
        4: 10
    }
    for e in effects:
        name = sc.remove_space(e.get("Name", ""))
        name = const.ENGRAVINGS_ABBR.get(name, name)
        level = e.get("Level")
        # AbilityStoneLevel 유무와 관계없이 Name + Level 은 engravings에 포함
        normal_parts.append(f"{name} ({level})")
        # AbilityStoneLevel이 있는 항목만 ability_stone에 추가로 포함
        if e.get("AbilityStoneLevel") is not None:
            temp_stone[name] = stone_level_dict[e['AbilityStoneLevel']]
    
    stone_parts = sorted(temp_stone.items(), key=lambda x: x[1], reverse=True)


    result["engravings"]     = normal_parts if normal_parts else None
    result["ability_stone"]  = ("".join([item[0] for item in stone_parts]) + " " + "".join(str(item[1]) for item in stone_parts))  if stone_parts  else None

    # ── ArmoryGem ──────────────────────────────────────────────────────────
    gem_section = data.get("ArmoryGem") or {}
    gems_list   = gem_section.get("Gems") or []

    level_counter = Counter(g["Level"] for g in gems_list)
    # 레벨 오름차순으로 정렬 후 "{N}레벨 {cnt}개" 형태로 조합
    gems_parts = [
        f"{lvl}레벨 {cnt}개"
        for lvl, cnt in sorted(level_counter.items())
    ]
    result["gems"] = " / ".join(gems_parts) if gems_parts else None

    # ── ArkPassive ─────────────────────────────────────────────────────────
    ark_passive = data.get("ArkPassive") or {}
    result["arkp_title"] = ark_passive.get("Title")

    # ── ArkGrid ────────────────────────────────────────────────────────────
    ark_grid = data.get("ArkGrid") or {}
    slots    = ark_grid.get("Slots") or []

    core_parts = [
        f"{s.get('Name')} ({s.get('Grade')}{s.get('Point')})"
        for s in slots
    ]
    result["arkg_cores"] = core_parts if core_parts else None

    return result


def char_result_to_embed(data: dict):
    gems_text = data['gems'] if data['gems'] is not None else "보석 미장착 중"

    embed_title = f"{data['char_name']} @ {data['server']}"
    
    arkg_cores = '\n'.join(data['arkg_cores']) if data['arkg_cores'] is not None else '없음'

    embed_desc = (
        f"{data['class']} (**{data['arkp_title']}**)"+"\n"
        f"스탯: 치 {data['crit']} | 특 {data['spec']} | 신 {data['swift']}"+"\n\n"
        f"아이템 레벨: **{data['item_lvl']}**"+"\n"
        f"전투력: **{data['combat_pwr']}**"+"\n\n"
        f"장착각인: {', '.join(data['engravings']) if data['engravings'] is not None else '없음'}"+"\n"
        f"돌: {data['ability_stone'] if data['ability_stone'] is not None else '없음'}"+"\n"
        f"보석: {gems_text}"+"\n\n"
        f"코어:"+"\n"
        f"{arkg_cores}"
    )

    embed = discord.Embed(
        title = embed_title,
        description = embed_desc,
        color = discord.Color.random()
    )

    embed.set_thumbnail(url = data['char_img_url'])

    return embed

def parse_siblings_list(data: list) -> list:
    result = []
    filtered_list = [char for char in data if char['CharacterLevel'] >= 60]

    sorted_list = sorted(
        filtered_list,
        key=lambda x: float(str(x.get('ItemAvgLevel', '0')).replace(',', '')),
        reverse = True
    )

    result = [
        f"**{char['CharacterName']}** @ {char['ServerName']} : **{char['ItemAvgLevel']}** {char['CharacterClassName']}"
        for char in sorted_list
    ]
    
    return result

def siblings_list_to_embed(data: list):
    embed_title = f"캐릭터 목록"
    embed_desc = "\n".join(data)
    embed = discord.Embed(
        title = embed_title,
        description = embed_desc,
        color = discord.Color.random()
    )
    return embed


# ==================================================================

if __name__ == "__main__":
    import json

    INPUT_FILE  = "test_basic.json"
    OUTPUT_FILE = "test_basic_parsed.json"

    with open(INPUT_FILE, "r", encoding="utf-8-sig") as f:
        raw = json.load(f)

    parsed = parse_character(raw)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(parsed, f, ensure_ascii=False, indent=2)

    print(f"파싱 완료 → {OUTPUT_FILE}")
    for k, v in parsed.items():
        print(f"  {k}: {v}")