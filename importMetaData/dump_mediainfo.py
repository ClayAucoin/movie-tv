"""
python dump_mediainfo.py "C:/Videos/MyMovie.mkv"

python "C:/_lib/data/_scripts_/py/_projects/ImportMetaData/dump_mediainfo.py" "M:/Movies/Watchmen (2009)/Watchmen (2009) [Director's Cut, 1080p, 5.1].mkv"
python "C:/_lib/data/_scripts_/py/_projects/ImportMetaData/dump_mediainfo.py" "M:/Movies/Watchmen (2009)/Watchmen (2009) [Theatrical Cut, 1080p, 5.1].mkv"

"""

from pymediainfo import MediaInfo
import sys
import os

def dump_mediainfo(file_path):
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return

    media_info = MediaInfo.parse(file_path)
    print(f"\n📄 Metadata for: {file_path}\n{'='*60}")

    for track in media_info.tracks:
        print(f"\n🎬 Track Type: {track.track_type}")
        print('-' * 60)
        for attr in dir(track):
            if not attr.startswith('_') and not callable(getattr(track, attr)):
                value = getattr(track, attr)
                if value not in [None, '', [], {}]:
                    print(f"{attr}: {value}")
        print('-' * 60)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python dump_mediainfo.py <media_file>")
    else:
        dump_mediainfo(sys.argv[1])
