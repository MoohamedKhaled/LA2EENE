import face_recognition
from flask import Flask, jsonify, request
import numpy
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate(
    "put ur project's key here"
)
firebase_admin.initialize_app(
    cred,
    {
        "projectId": "put ur project's id here",
    },
)
db = firestore.client()


ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

app = Flask(__name__)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/finderPost", methods=["POST"])
def upload_image_finder():
    if "file" not in request.files:
        return jsonify({"massage": "you did not send file"})

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"massage": "file is empty"})
    
    ID=request.form['ID']

    if file and allowed_file(file.filename):
        return finder_post(file, ID)


@app.route("/seekerPost", methods=["POST"])
def upload_image_seeker():
    if "file" not in request.files:
        return jsonify({"massage": "you did not send file"})

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"massage": "file is empty"})
    
    ID=request.form['ID']

    if file and allowed_file(file.filename):
        return seeker_post(file, ID)

#someone find a person and he dont know his/her name 
def finder_post(file_stream, ID):
    # this function searching in seeker posts
    # encode the image that u take from post
    unknown_image = face_recognition.load_image_file(file_stream)
    vector_unknown = face_recognition.face_encodings(unknown_image)[0]
    # start comparing between this vector and the known vetcors from firestore
    result = False
    vectors_known_stream = db.collection("known_vectors")
    # stream all the vectors in known vector
    docs = vectors_known_stream.stream()
    for doc in docs:
        vector_known = doc.to_dict()
        # convert list into np array to deal with compare function
        vector_known_list = vector_known["vector"]
        vector_known_np = numpy.array(vector_known_list)
        result = face_recognition.compare_faces([vector_unknown], vector_known_np)[0]
        if result == True:
            break
    if result == True:
        return jsonify({"result": True})
    else:
        # if there is no known_vector that same as unknown so upload this vector so we can use it again
        # convert np array vector to list to upload to firestore
        vector_unknown_list = vector_unknown.tolist()
        doc_ref = db.collection("unknown_vectors").document(ID)
        doc_ref.set({"ID": ID, "vector": vector_unknown_list})
        return jsonify({"result": False})

#someone search for person and he know his/her name 
def seeker_post(file_stream, ID):
    known_image = face_recognition.load_image_file(file_stream)
    vector_known = face_recognition.face_encodings(known_image)[0]
    result = False
    vectors_unknown_stream = db.collection("unknown_vectors")
    docs = vectors_unknown_stream.stream()
    for doc in docs:
        vector_unknown = doc.to_dict()
        vector_unknown_list = vector_unknown["vector"]
        vector_unknown_np = numpy.array(vector_unknown_list)
        result = face_recognition.compare_faces([vector_known], vector_unknown_np)[0]
        if result == True:
            break
    if result == True:
        return jsonify({"result": True})
    else:
        vector_known_list = vector_known.tolist()
        doc_ref = db.collection("known_vectors").document(ID)
        doc_ref.set({"ID": ID, "vector": vector_known_list})
        return jsonify({"massage": False})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
