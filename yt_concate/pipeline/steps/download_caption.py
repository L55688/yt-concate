from yt_dlp import YoutubeDL
import requests
import webvtt                                  # 若拿到的是 .vtt 需轉 .srt
import os

from .step import Step, StepException


class DownloadCaption(Step):
    def process(self, data, inputs):
        ydl_opts = {
            'writesubtitles': True,
          'writeautomaticsub': True,
           'skip_download': True,  # 不抓影片本身
            'subtitleslangs': ['en'],
            'outtmpl': f'%(id)s.%(ext)s',
            'quiet': True,  # 關掉多餘輸出&#xff0c;視需要保留
            'subtitlesformat': 'srt',
            'extractor_args': {
                'youtube': ['player_client=android']
            }
        }

        for url in data:
            try:
                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)

                # ① 先找自動字幕 (automatic_captions)。若要手動上傳字幕請改用 info["subtitles"]
                caps = info.get("automatic_captions", {})
                lang = "en"  # 目標語言
                if lang not in caps:
                    raise StepException(f"{url} 無自動英文字幕")

                # ② 找副檔名為 srt 的串流&#xff1b;沒有就抓第一個 (通常是 webvtt)
                caption_streams = caps[lang]
                srt_stream = next((c for c in caption_streams if c["ext"] == "srt"), caption_streams[0])

                # ③ 下載字幕檔
                resp = requests.get(srt_stream["url"], timeout=15)
                resp.raise_for_status()

                # ④ 若拿到 .vtt → 轉成 .srt
                ext = srt_stream["ext"]
                if ext == "vtt":
                    tmp_path = "tmp.vtt"
                    with open(tmp_path, "w", encoding="utf-8") as f:
                        f.write(resp.text)
                    webvtt.WebVTT().read(tmp_path).save_as_srt("Output.srt")
                    os.remove(tmp_path)
                else:  # 已經是 srt
                    with open("Output.srt", "w", encoding="utf-8") as f:
                        f.write(resp.text)

                # ⑤ 如需字串在記憶體自行使用 caption_text 變數
                caption_text = resp.text
                print(caption_text[:500])  # 範例&#xff1a;只印前 500 字
                break  # 跟你原本一樣處理第一支即可

            except Exception as e:
                raise StepException(str(e))