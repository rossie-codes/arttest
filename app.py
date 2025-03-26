import os
import cv2
import numpy as np
import random
from PIL import Image
from flask import Flask, render_template, request, jsonify
#from flask_ngrok import run_with_ngrok
#from pyngrok import ngrok


app = Flask(__name__, template_folder='templates', static_folder='static')
#run_with_ngrok(app)
#ngrok.set_auth_token("2aWldRt1Mxl5OxPKypgE0aOZS1l_46tB4Fy8Ka21cti2G1VdN")


#color-------------------------------------------------------------
def is_complementary_color(pixel):
    if len(pixel) == 3:
        r, g, b = pixel
        return abs(r - g) > 100 or abs(b - r) > 100 or abs(r - b) > 100 or abs(g - r) > 100

def is_complementary_split(image_path):
    img = Image.open(image_path)
    img = img.convert("RGB")
    pixels = list(img.getdata())
    complementary_colors = [pixel for pixel in pixels if is_complementary_color(pixel)]
    return len(complementary_colors) >= 2

def is_single_color(image_path):
    img = Image.open(image_path)
    img = img.convert("RGB")
    pixels = list(img.getdata())
    unique_colors = set(pixels)
    return len(unique_colors) == 1

def is_black_and_color(image_path):
    img = Image.open(image_path)
    img = img.convert("RGB")
    pixels = list(img.getdata())

    black = (0, 0, 0)
    other_color = None
    for pixel in pixels:
        if pixel != black:
            if other_color is None:
                other_color = pixel
            elif pixel != other_color:
                return False
    return other_color is not None

def is_three_tone(image_path):
    img = Image.open(image_path).convert('L')
    histogram = img.histogram()
    shadow_pixels = sum(histogram[:85])
    midtone_pixels = sum(histogram[85:170])
    highlight_pixels = sum(histogram[170:])
    total_pixels = img.width * img.height
    return (shadow_pixels > 0.1 * total_pixels and
            midtone_pixels > 0.1 * total_pixels and
            highlight_pixels > 0.1 * total_pixels)

def is_double_complementary_rect(image_path):
    img = Image.open(image_path)
    img = img.convert("RGB")
    pixels = list(img.getdata())

    color_set = set(pixels)
    if len(color_set) == 4:
        complementary_colors = [pixel for pixel in color_set if is_complementary_color(pixel)]
        return len(complementary_colors) >= 2

    return False
#color-------------------------------------------------------------

#feature-------------------------------------------------------------
if not os.path.exists('uploads'):
    os.makedirs('uploads')

def edge_detection(gray_img):
    edges = cv2.Canny(gray_img, 50, 150)
    edge_score = np.mean(edges)
    return edge_score

def shape_features(gray_img):
    _, thresh = cv2.threshold(gray_img, 127, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    shape_score = 0
    for contour in contours:
        hu_moments = cv2.HuMoments(cv2.moments(contour)).flatten()
        shape_score += sum([-np.sign(hu) * np.log10(np.abs(hu)) if hu != 0 else 0 for hu in hu_moments])
    return shape_score

def grayscale_image(img_path):
    img = cv2.imread(img_path)
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray_img = cv2.resize(gray_img, (1024, 512))
    return gray_img

def calculate_image_score(img_path):
    gray_img = grayscale_image(img_path)
    if gray_img is None:
      return None
    edge_score = edge_detection(gray_img)
    shape_score = shape_features(gray_img)
    max_edge_score = 20.0
    max_shape_score = 3500.0
    normalized_edge_score = (edge_score / max_edge_score) * 100
    normalized_shape_score = (shape_score / max_shape_score) * 100
    normalized_edge_score = min(normalized_edge_score, 100)
    normalized_shape_score = min(normalized_shape_score, 100)
    normalized_edge_score = int(normalized_edge_score)
    normalized_shape_score = int(normalized_shape_score)
    return {'EdgeScore': normalized_edge_score, 'ShapeScore': normalized_shape_score}
#feature-------------------------------------------------------------

#creativity-------------------------------------------------------------
imgur_links = [
    'https://i.imgur.com/OqiU6Mr.jpg',
    'https://i.imgur.com/kmhKcQW.jpg',
    'https://i.imgur.com/l1hQgpj.jpg',
    'https://i.imgur.com/KDgDzeu.jpg',
    'https://i.imgur.com/PwilH21.jpg',
    'https://i.imgur.com/ZypOBpw.jpg',
    'https://i.imgur.com/kANk6Bm.jpg',
    'https://i.imgur.com/VdXUQ8j.jpg',
    'https://i.imgur.com/RzVjnPC.png',
    'https://i.imgur.com/IGohqxc.jpg',
]
image_order_count = {link: {'order': 0, 'score': 0} for link in imgur_links}
selected_links = []
#creativity-------------------------------------------------------------

#history-------------------------------------------------------------

#history-------------------------------------------------------------



#------------------------------------------------------------------
@app.route('/', methods=['GET', 'POST'])
def index():
  global selected_links,imgur_links,questions
  if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'})

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'})

        # 取得目前檔案所在的目錄路徑
        current_directory = os.path.dirname(os.path.abspath(__file__))

        # 指定暫存圖片的路徑
        temp_image_path = os.path.join(current_directory, 'temp_image.jpg')
        file.save(temp_image_path)


        ColorScore = 60  # 假設初始分數是60

        # 如果為 True，則增加分數
        if is_complementary_split(temp_image_path):
            ColorScore += 20
            if ColorScore > 100:  # 檢查分數是否超過100
                ColorScore = 100  # 如果超過，將分數設為100

        if is_single_color(temp_image_path):
            ColorScore += 20
            if ColorScore > 100:
                ColorScore = 100

        if is_black_and_color(temp_image_path):
            ColorScore += 20
            if ColorScore > 100:
                ColorScore = 100

        if is_three_tone(temp_image_path):
            ColorScore += 20
            if ColorScore > 100:
                ColorScore = 100

        if is_double_complementary_rect(temp_image_path):
            ColorScore += 20
            if ColorScore > 100:
                ColorScore = 100


         # 刪除暫存的圖片
        os.remove(temp_image_path)
        # 同時返回計算結果和隨機圖片
        selected_links = random.sample(imgur_links, 4)
        return jsonify({'ColorScore': ColorScore, 'imgur_links': selected_links})
  else:
        # 顯示隨機選取的圖片
        selected_links = random.sample(imgur_links, 4)
        return render_template('index.html', imgur_links=selected_links)


@app.route('/sort', methods=['POST'])
def sort_images():
    global image_order_count
    links = request.json.get('order', [])
    for i, link in enumerate(links, 1):
        if link in image_order_count:
            image_order_count[link]['order'] = i
            if i == 1:
                image_order_count[link]['score'] += 3
            elif i == 2:
                image_order_count[link]['score'] += 2
            elif i == 3:
                image_order_count[link]['score'] += 1
            else:
                image_order_count[link]['score'] += 0
    sorted_images = sorted(
        image_order_count,
        key=lambda x: (
            image_order_count.get(x, {'score': 0})['score'],
            image_order_count.get(x, {'order': 0})['order']
        ),
        reverse=True
    )
    first_sorted_image = sorted_images[0] if sorted_images else None
    creativity_score = {}
    for i, link in enumerate(links, 1):
        if i == 1 and link == first_sorted_image:
            creativity_score[link] = 30
        elif 2 <= i <= 4 and link in selected_links:
            creativity_score[link] = 30
        elif 5 <= i <= 7 and link in selected_links:
            creativity_score[link] = 30
        elif 8 <= i <= 10 and link in selected_links:
            creativity_score[link] = 30
        else:
            creativity_score[link] = 0
    total_creativity_score = sum(creativity_score.values())
    total_creativity_score = min(total_creativity_score, 100)
    sorted_image_rankings = {link: i + 1 for i, link in enumerate(sorted_images)}
    return jsonify({'status': 'success', 'sorted_image_rankings': sorted_image_rankings, 'total_creativity_score': total_creativity_score})


@app.route('/analyze', methods=['POST'])
def analyze():
    uploaded_file = request.files['file']
    if uploaded_file.filename != '':
        img_path = 'uploads/' + uploaded_file.filename
        uploaded_file.save(img_path)
        FeatureScore = calculate_image_score(img_path)
        if FeatureScore is not None:
            return jsonify(FeatureScore)
        else:
            return jsonify({'error': 'Failed to process the image.'})
    return jsonify({'error': 'No file uploaded.'})


if __name__ == "__main__":
    app.run()
 