import twitter, os, json, time, tempfile, contextlib, sys, io

from PIL import Image
from minio import Minio
from minio.error import ResponseError

@contextlib.contextmanager
def nostdout():
    save_stdout = sys.stdout
    sys.stdout = io.BytesIO()
    yield
    sys.stdout = save_stdout

minioClient = Minio(os.environ['minio_hostname'],
                  access_key=os.environ['minio_access_key'],
                  secret_key=os.environ['minio_secret_key'],
                  secure=False)

api = twitter.Api(
    consumer_key=os.environ['consumer_key'],
    consumer_secret=os.environ['consumer_secret'],
    access_token_key=os.environ['access_token'],
    access_token_secret=os.environ['access_token_secret']
)

def handle(data):
    data = json.loads(data)
    filename = tempfile.gettempdir() + '/' + str(int(round(time.time() * 1000))) + '.jpg'
    in_reply_to_status_id = data['status_id']

    with nostdout():
        minioClient.fget_object('colorization', data['image'], filename)

    with open(filename, 'rb') as image:
        size = os.fstat(image.fileno()).st_size
        if size > 5 * 1048576:
            maxsize = (1028, 1028)
            im = Image.open(filename)
            im.thumbnail(maxsize, Image.ANTIALIAS)
            im = im.convert("RGB")
            scaled_filename = filename.split('.')[0] + '_scaled.jpg'
            im.save(scaled_filename, "JPEG")
            image = open(filename.split('.')[0] + '_scaled.jpg', 'rb')

        status = api.PostUpdate("Hey, here's your colored image!",
            media=image,
            auto_populate_reply_metadata=True,
            in_reply_to_status_id=in_reply_to_status_id)
        return status
        image.close()
