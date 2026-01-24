import json
import datetime
import os

# 读取数据
def load_data():
    with open('data.json', 'r', encoding='utf-8') as f:
        return json.load(f)

# 时间字符串转秒
def time_str_to_seconds(time_str):
    try:
        parts = list(map(int, time_str.split(':')))
        seconds = 0
        for i, part in enumerate(parts):
            seconds += part * (60 ** (len(parts) - 1 - i))
        return seconds
    except:
        return 0

# 构建B站链接
def build_video_url(bvid, p, time_str):
    seconds = time_str_to_seconds(time_str)
    milliseconds = seconds * 1000
    url = f"https://www.bilibili.com/video/{bvid}/?"
    params = []
    
    if str(p) != '1':
        params.append(f"p={p}")
    
    params.append(f"t={seconds}")
    params.append(f"start_progress={milliseconds}")
    params.append("share_source=MARK_POINT")
    
    return url + "&".join(params)

# 生成 HTML
def generate_html():
    data = load_data()
    
    # 1. 预处理数据：按发布时间降序排序
    episodes = sorted(data, key=lambda x: x['pubdate'], reverse=True)
    
    # 2. 构建 Timeline HTML
    timeline_html = ""
    for episode in episodes:
        date_obj = datetime.datetime.fromisoformat(episode['pubdate'].replace('Z', '+00:00'))
        date_str = date_obj.strftime('%Y/%m/%d')
        
        segments_html = ""
        for record in episode['records']:
            url = build_video_url(episode['bvid'], record['p'], record['time'])
            segments_html += f"""
            <a href="{url}" target="_blank" rel="noopener noreferrer" class="game-segment">
                <span class="segment-time">{record['p']}#{record['time']}</span>
                <span class="segment-name">{record['name']}</span>
            </a>
            """
            
        timeline_html += f"""
        <div class="timeline-item" data-episode="{episode['bvid']}">
            <div>
                <div class="timeline-date">{date_str}</div>
                <a href="https://www.bilibili.com/video/{episode['bvid']}/" target="_blank" rel="noopener noreferrer" class="timeline-video-link">
                    {episode['title'][:50]}...
                </a>
            </div>
            <div class="timeline-games">
                {segments_html}
            </div>
        </div>
        """

    # 3. 构建 Games Grid HTML
    game_map = {}
    for episode in episodes:
        for record in episode['records']:
            if record['name'] not in game_map:
                game_map[record['name']] = []
            game_map[record['name']].append({
                'episode': episode,
                'record': record
            })
            
    # 对每个游戏内的记录排序
    for game_name in game_map:
        game_map[game_name].sort(key=lambda x: (
            x['episode']['pubdate'][:10],
            int(x['record']['p']),
            time_str_to_seconds(x['record']['time'])
        ))

    # 对游戏卡片排序（按该游戏最后一次出现的时间降序）
    sorted_games = sorted(game_map.keys(), key=lambda k: game_map[k][-1]['episode']['pubdate'], reverse=True)

    games_grid_html = ""
    for game_name in sorted_games:
        items_html = ""
        for item in game_map[game_name]:
            date_obj = datetime.datetime.fromisoformat(item['episode']['pubdate'].replace('Z', '+00:00'))
            date_str = date_obj.strftime('%Y/%m/%d')
            url = build_video_url(item['episode']['bvid'], item['record']['p'], item['record']['time'])
            
            items_html += f"""
            <a href="{url}" target="_blank" rel="noopener noreferrer" class="episode-item">
                <span class="episode-date">{date_str}</span>
                <span class="episode-time">{item['record']['p']}#{item['record']['time']}</span>
            </a>
            """
            
        games_grid_html += f"""
        <div class="game-card" data-game="{game_name}">
            <div class="game-title">{game_name}</div>
            <div class="episode-list">
                {items_html}
            </div>
        </div>
        """

    # 4. 读取模板并替换
    with open('template.html', 'r', encoding='utf-8') as f:
        template = f.read()
        
    final_html = template.replace('<!-- {{ GAMES_GRID }} -->', games_grid_html)
    final_html = final_html.replace('<!-- {{ TIMELINE_ITEMS }} -->', timeline_html)
    
    # 5. 写入 index.html
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(final_html)
        
    print("Build complete: index.html generated.")

if __name__ == "__main__":
    generate_html()