from flask import Flask, request, jsonify, send_file, abort, render_template
import os
import shutil
from datetime import datetime

app = Flask(__name__)
STORAGE_DIR = os.path.join(os.path.dirname(__file__), 'file_storage')


def get_valid_path(user_path):
    base = os.path.abspath(STORAGE_DIR)
    target = os.path.abspath(os.path.join(base, user_path))
    return target if target.startswith(base) else None


def list_directory(path, url_path):
    items = []
    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        stat = os.stat(item_path)
        is_dir = os.path.isdir(item_path)

        items.append({
            'name': item,
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'is_directory': is_dir,
            'url': os.path.join(url_path, item) + ('/' if is_dir else '')
        })
    return items


@app.route('/', defaults={'path': ''}, methods=['GET'])
@app.route('/<path:path>', methods=['GET', 'PUT', 'DELETE', 'HEAD'])
def handle_request(path):
    full_path = get_valid_path(path)
    if not full_path:
        abort(403)

    if request.method == 'GET':
        if os.path.isdir(full_path):
            try:
                items = list_directory(full_path, path)
                if 'text/html' in request.headers.get('Accept', ''):
                    return render_template('index.html',
                                           path=path,
                                           items=items)
                return jsonify(items)
            except FileNotFoundError:
                abort(404)
        elif os.path.isfile(full_path):
            return send_file(full_path)
        abort(404)

    if request.method == 'PUT':
        dir_path = os.path.dirname(full_path)
        os.makedirs(dir_path, exist_ok=True)
        if path.endswith('/') or not os.path.splitext(path)[1]:
            os.makedirs(full_path, exist_ok=True)
            return jsonify({"status": "directory created"}), 201
        data = request.get_data()
        if not data:
            return jsonify({"error": "No content provided"}), 400
        with open(full_path, 'wb') as f:
            f.write(data)
        return jsonify({"status": "file created"}), 201

    elif request.method == 'HEAD':
        if os.path.isfile(full_path):
            stat = os.stat(full_path)
            headers = {
                'Content-Length': stat.st_size,
                'Last-Modified': datetime.fromtimestamp(stat.st_mtime).strftime('%a, %d %b %Y %H:%M:%S GMT')
            }
            return ('', 200, headers)
        abort(404)

    elif request.method == 'DELETE':
        if not os.path.exists(full_path):
            return jsonify({"error": "Resource not found"}), 404

        try:
            if os.path.isfile(full_path):
                os.remove(full_path)
                return jsonify({"status": "File deleted successfully"}), 200
            else:
                shutil.rmtree(full_path)
                return jsonify({"status": "Directory deleted successfully"}), 200
        except Exception as e:
            return jsonify({"status": "error"}), 500

    abort(405)


if __name__ == '__main__':
    os.makedirs(STORAGE_DIR, exist_ok=True)
    app.run(debug=True)