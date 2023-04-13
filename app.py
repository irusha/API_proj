import os
import shutil

from flask import Flask, render_template, request, jsonify
import cv2
from werkzeug.utils import secure_filename
from moviepy.editor import VideoFileClip, concatenate_videoclips

app = Flask(__name__)


def make_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)


def trim_video(video, file_name, start, end):
    clip = VideoFileClip(video)
    clip_no_sound = clip.without_audio()
    clip1 = clip_no_sound.subclip(start, end)
    clip1.write_videofile(file_name, codec='libx264')
    clip.close()


def video_duration(file):
    video = cv2.VideoCapture(file)
    fps = video.get(cv2.CAP_PROP_FPS)  # OpenCV v2.x used "CV_CAP_PROP_FPS"
    frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps
    video.release()
    return duration


def generate_thumbnail(file, position, destination_folder, destination_file):
    make_folder(destination_folder)
    vidcap = cv2.VideoCapture(file)

    print("Started generating the thumbnail")

    width = int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    frame_count = vidcap.get(cv2.CAP_PROP_FRAME_COUNT)
    frame = int(frame_count * position)
    res, im_ar = vidcap.read()

    count = 0

    while count < frame:
        res, im_ar = vidcap.read()
        count += 1

    im_ar = cv2.resize(im_ar, (width, height), 0, 0, cv2.INTER_LINEAR)
    cv2.imwrite(destination_folder + destination_file, im_ar)

    print("Successfully generated", destination_folder + destination_file)


def combine_videos(clip_paths, destination, file_name):
    clips = [VideoFileClip(c) for c in clip_paths]
    make_folder(destination)
    final_clip = concatenate_videoclips(clips, method="compose")
    final_clip.write_videofile(destination + file_name)
    for clip in clips:
        clip.close()


def generate_preview(file, duration, destination_folder, destination_file):
    dirpath = destination_folder + "temp"
    make_folder(dirpath)
    make_folder(destination_folder + "preview")

    for i in range(10):
        fraction = i / 10
        trim_video(file, destination_folder + 'temp/edited_%s.mp4' % i, duration * fraction, (duration * fraction) + 1)

    combine_videos(
        (destination_folder + "temp/edited_%s.mp4" % s for s in range(10)),
        destination_folder + "preview/", destination_file)

    if os.path.exists(dirpath) and os.path.isdir(dirpath):
        shutil.rmtree(dirpath)


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == "POST":
        uploaded_files = request.files.getlist("file")

        if len(uploaded_files) == 0:
            return "InvalidRequest"
        elif uploaded_files[0].content_type is None:
            return "NoFilesFound"

        failed_files = {}

        for curr_file in uploaded_files:
            file_name = secure_filename(curr_file.filename)
            _file = "static/%s/video/" % file_name + file_name

            file_type = curr_file.content_type.split('/')[0]
            print(file_type)

            if file_type != "video":
                failed_files[file_name] = "InvalidType"
                if os.path.exists("static/" + file_name) and os.path.isdir("static/" + file_name):
                    shutil.rmtree("static/" + file_name)
                continue

            make_folder("static/%s/video/" % file_name)
            curr_file.save(_file)

            try:
                generate_thumbnail(_file, 0.2, "static/%s/thumbnail/" % file_name, file_name + ".jpg")
                duration = video_duration(_file)
                generate_preview(_file, duration, "static/%s/" % file_name,
                                 file_name + "preview.mp4")

            except:
                failed_files[file_name] = "ParseError"
                if os.path.exists("static/" + file_name) and os.path.isdir("static/" + file_name):
                    shutil.rmtree("static/" + file_name)

        return jsonify({
            "url": request.url + "static/out.mp4",
            "failed_files": failed_files
        })

    else:
        return render_template("index.html")
