from flask import Flask, render_template, request, jsonify
import cv2
from werkzeug.utils import secure_filename
from moviepy.editor import VideoFileClip, concatenate_videoclips

app = Flask(__name__)


def trim_video(video, file_name, start, end):
    clip = VideoFileClip(video).without_audio()
    clip1 = clip.subclip(start, end)
    clip1.write_videofile(file_name, codec='libx264')


def video_duration(file):
    video = cv2.VideoCapture(file)
    fps = video.get(cv2.CAP_PROP_FPS)      # OpenCV v2.x used "CV_CAP_PROP_FPS"
    frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count/fps
    return duration


def combine_videos(clip_paths):
    clips = [VideoFileClip(c) for c in clip_paths]
    final_clip = concatenate_videoclips(clips, method="compose")
    final_clip.write_videofile("out.mp4")


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == "POST":
        uploaded_file = request.files['file']
        _file = secure_filename(uploaded_file.filename)
        uploaded_file.save(_file)
        duration = video_duration(_file)
        trim_video(_file, 'edited.mp4', duration * 0.25, (duration * 0.25) + 2)
        trim_video(_file, 'edited2.mp4', duration * 0.5, (duration * 0.5) + 2)
        trim_video(_file, 'edited3.mp4', duration * 0.75, (duration * 0.75) + 2)
        combine_videos(("edited.mp4", "edited2.mp4", "edited3.mp4"))
        return jsonify({
            "url": request.url + "edited.mp4",
            "duration": duration
        })

    else:
        return render_template("index.html")

