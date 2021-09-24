import requests,json
from PIL import ImageFont,Image,ImageDraw
from hoshino.service import Service
from hoshino.typing import HoshinoBot, CQEvent
from collections import defaultdict
import os
from hoshino import Service, priv, util
from hoshino.typing import *
from base64 import b64encode
from io import BytesIO

sv_help = '''
- [原神十连] 来发十连
- [原神单抽] 来一发
- [切换原神卡池 常驻/角色/武器] 切换卡池
- [查看原神卡池] 查看当前卡池
- [祈愿详情] 获取抽卡统计数据
- [武器定轨 （名字）] 定轨
- [查询定轨] 看看自己定轨了什么武器
'''.strip()

sv = Service('原神抽卡')

@sv.on_fullmatch(["帮助原神抽卡"])
async def bangzhu(bot, ev):
    await bot.send(ev, sv_help, at_sender=True)

#授权码请自行获取
authcode = ''

_pool_config_file = os.path.expanduser('~/.hoshino/genshin_group_pool_config.json')
_group_pool = {}
POOL = ('常驻', '角色', '武器')
DEFAULT_POOL = POOL[0]
try:
    with open(_pool_config_file, encoding='utf8') as f:
        _group_pool = json.load(f)
except FileNotFoundError as e:
    sv.logger.warning('genshin_group_pool_config.json not found, will create when needed.')
_group_pool = defaultdict(lambda: DEFAULT_POOL, _group_pool)

def dump_pool_config():
    with open(_pool_config_file, 'w', encoding='utf8') as f:
        json.dump(_group_pool, f, ensure_ascii=False)

@sv.on_prefix(('切换原神卡池', '选择原神卡池'))
async def set_pool(bot, ev: CQEvent):
    name = util.normalize_str(ev.message.extract_plain_text())
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.finish(ev, '只有群管理才能切换卡池', at_sender=True)
        return
    POOL_NAME_TIP = '请选择以下卡池\n> 选择原神卡池 常驻\n> 选择原神卡池 角色\n> 选择原神卡池 武器'
    if not name:
        await bot.finish(ev, POOL_NAME_TIP, at_sender=True)
    elif name in ('常驻', '常驻池'):
        name = '常驻'
    elif name in ('角色', '角色池', '角色up', '角色up池'):
        name = '角色'
    elif name in ('武器', '武器池', '武器up', '武器up池'):
        name = '武器'
    else:
        await bot.send(ev, f'未找到{name}', at_sender=True)
        return
    gid = str(ev.group_id)
    _group_pool[gid] = name
    dump_pool_config()
    await bot.send(ev, f'卡池已切换为{name}池', at_sender=True)

@sv.on_rex('查看原神卡池')
async def see_pool(bot,ev):
    gid = str(ev['group_id'])
    url = 'https://gacha.kyaru.cn/api/PrayInfo/GetPondInfo'
    headers = {'authorzation':authcode}
    res = requests.get(url=url, headers=headers)
    r = json.loads(res.content)
    arm = r['data']['arm']['star5UpList']
    arms = ['']
    for i in arm:
        arms.append(i['goodsName'])
    arm1 = r['data']['arm']['star4UpList']
    arms1 = ['']
    for i in arm1:
        arms1.append(i['goodsName'])
    role = r['data']['role']['star5UpList']
    roles = ['']
    for i in role:
        roles.append(i['goodsName'])
    role1 = r['data']['role']['star4UpList']
    roles1 = ['']
    for i in role1:
        roles1.append(i['goodsName'])
    await bot.send(ev, f'当前角色池up：\n五星：{roles}\n四星：{roles1}\n当前武器池up：\n五星：{arms}\n四星：{arms1}', at_sender=True)

@sv.on_rex('原神十连')
async def gacha_ten(bot, ev):
    gid = str(ev['group_id'])
    uid = str(ev['user_id'])
    if not gid in _pool_config_file:
        _pool = ('常驻')
    _pool = _group_pool[gid]
    if _pool in ('常驻'):
        url = 'https://gacha.kyaru.cn/api/PermPray/PrayTen?memberCode=' + uid + '&toBase64=true'
    elif _pool in ('角色'):
        url = 'https://gacha.kyaru.cn/api/RolePray/PrayTen?memberCode=' + uid + '&toBase64=true'
    elif _pool in ('武器'):
        url = 'https://gacha.kyaru.cn/api/ArmPray/PrayTen?memberCode=' + uid + '&toBase64=true'
    headers = {'authorzation':authcode}
    res = requests.get(url=url, headers=headers)
    r = json.loads(res.content)
    base64 = r['data']['imgBase64']
    result_buffer = BytesIO()
    imgmes = 'base64://' + base64
    resultmes = f"[CQ:image,file={imgmes}]"
    await bot.finish(ev,resultmes, at_sender=False)

@sv.on_rex('原神单抽')
async def gacha_one(bot, ev):
    gid = str(ev['group_id'])
    uid = str(ev['user_id'])
    if not gid in _pool_config_file:
        _pool = ('常驻')
    _pool = _group_pool[gid]
    if _pool in ('常驻'):
        url = 'https://gacha.kyaru.cn/api/PermPray/PrayOne?memberCode=' + uid + '&toBase64=true'
    elif _pool in ('角色'):
        url = 'https://gacha.kyaru.cn/api/RolePray/PrayOne?memberCode=' + uid + '&toBase64=true'
    elif _pool in ('武器'):
        url = 'https://gacha.kyaru.cn/api/ArmPray/PrayOne?memberCode=' + uid + '&toBase64=true'
    headers = {'authorzation':authcode}
    res = requests.get(url=url, headers=headers)
    r = json.loads(res.content)
    base64 = r['data']['imgBase64']
    result_buffer = BytesIO()
    imgmes = 'base64://' + base64
    resultmes = f"[CQ:image,file={imgmes}]"
    await bot.finish(ev,resultmes, at_sender=False)

@sv.on_rex('祈愿详情')
async def gacha_info(bot, ev):
    gid = str(ev['group_id'])
    uid = str(ev['user_id'])
    url = 'https://gacha.kyaru.cn/api/PrayInfo/GetMemberPrayDetail?memberCode=' + uid
    headers = {'authorzation':authcode}
    res = requests.get(url=url, headers=headers)
    r = json.loads(res.content)
    d = r['data']
    msg1 = f'''
总抽卡数：{d['totalPrayTimes']}
五星数量：{d['star5Count']}
五星概率：{d['star5Rate']}
四星数量：{d['star4Count']}
四星概率：{d['star4Rate']}'''
    msg2 = f'''
角色池
抽卡总数：{d['rolePrayTimes']}
距离大保底：{d['role180Surplus']}
距离小保底：{d['role90Surplus']}
距离四星保底：{d['role10Surplus']}
五星数量：{d['roleStar5Count']}
五星概率：{d['roleStar5Rate']}
四星数量：{d['roleStar4Count']}
四星概率：{d['roleStar4Rate']}'''
    msg3 = f'''
武器池
抽卡总数：{d['armPrayTimes']}
距离五星保底：{d['arm80Surplus']}
距离四星保底：{d['arm10Surplus']}
定轨命定值：{d['armAssignValue']}
五星数量：{d['armStar5Count']}
五星概率：{d['armStar5Rate']}
四星数量：{d['armStar4Count']}
四星概率：{d['armStar4Rate']}'''
    msg4 = f'''
常驻池
抽卡总数：{d['permPrayTimes']}
距离五星保底：{d['perm90Surplus']}
距离四星保底：{d['perm10Surplus']}
五星数量：{d['permStar5Count']}
五星概率：{d['permStar5Rate']}
四星数量：{d['permStar4Count']}
四星概率：{d['permStar4Rate']}'''
    data_all = []
    data1 ={
            "type": "node",
            "data": {
                "name": '原神抽卡管家',
                "uin": '2854196310',
                "content": msg1
            }
            }
    data2 ={
            "type": "node",
            "data": {
                "name": '原神抽卡管家',
                "uin": '2854196306',
                "content": msg2
            }
            }
    data3 ={
            "type": "node",
            "data": {
                "name": '原神抽卡管家',
                "uin": '2854196314',
                "content": msg3
            }
            }
    data4 ={
            "type": "node",
            "data": {
                "name": '原神抽卡管家',
                "uin": '2854196320',
                "content": msg4
            }
            }            
    data_all=[data1,data2,data3,data4]
    await bot.send_group_forward_msg(group_id=ev['group_id'], messages=data_all)

@sv.on_prefix(('武器定轨', '定轨'))
async def arm_star(bot, ev):
    name = util.normalize_str(ev.message.extract_plain_text())
    gid = str(ev['group_id'])
    uid = str(ev['user_id'])
    url = f'https://gacha.kyaru.cn/api/PrayInfo/SetMemberAssign?memberCode={uid}&goodsName={name}'
    headers = {'authorzation':authcode}
    res = requests.post(url=url, headers=headers)
    r = json.loads(res.content)
    msg = r['message']
    await bot.finish(ev, msg, at_sender=True)

@sv.on_rex('查询定轨')
async def star_info(bot, ev):
    gid = str(ev['group_id'])
    uid = str(ev['user_id'])
    url = 'https://gacha.kyaru.cn/api/PrayInfo/GetMemberAssign?memberCode=' + uid
    headers = {'authorzation':authcode}
    res = requests.get(url=url, headers=headers)
    r = json.loads(res.content)
    msg = r['data']['goodsName']
    await bot.finish(ev, msg, at_sender=True)
