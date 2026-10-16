"""Proof photos: cleaning (EXIF, size), bonus points, signed URLs, permissions and cheers."""

import io
import time
from urllib.parse import parse_qs, urlparse

from PIL import Image

from app.storage import S3Storage


def jpeg(width: int = 3000, height: int = 2000, orientation: int | None = None) -> bytes:
    """A camera-like JPEG with metadata (maker, model and, optionally, rotation)."""
    image = Image.new("RGB", (width, height), (200, 60, 120))
    exif = Image.Exif()
    exif[0x010F] = "PhoneMaker"  # Make
    exif[0x0110] = "PhoneModel"  # Model
    if orientation:
        exif[0x0112] = orientation
    output = io.BytesIO()
    image.save(output, "JPEG", exif=exif.tobytes())
    return output.getvalue()


def fetch(client, url: str):
    return client.get(url)


def test_photo_adds_bonus_and_is_cleaned(rafael, ana):
    workout = rafael.checkin(minutes=30).json()["workout"]
    assert workout["points"] == 10

    response = rafael.upload_photo(workout["id"], jpeg(orientation=6))  # rotated 90° by the camera
    assert response.status_code == 200
    body = response.json()
    assert body["workout"]["has_photo"] is True
    assert body["workout"]["points"] == 15  # 10 + photo bonus
    assert body["scoreboard"]["players"][0]["points"] == 15
    assert body["feedback"]["message"] == "Você passou na frente!"

    picture = fetch(rafael.client, body["workout"]["photo_url"])
    assert picture.status_code == 200 and picture.headers["content-type"] == "image/jpeg"
    stored = Image.open(io.BytesIO(picture.content))
    assert stored.size == (1067, 1600)  # orientation applied, longest side capped at 1600
    assert dict(stored.getexif()) == {}  # no metadata left (location included)

    # The duo sees it too, through their own signed URL.
    listed = ana.get("/workouts").json()[0]
    assert listed["has_photo"] and fetch(ana.client, listed["photo_url"]).status_code == 200


def test_signed_urls_cannot_be_forged_or_reused_late(rafael, monkeypatch):
    workout_id = rafael.checkin().json()["workout"]["id"]
    url = rafael.upload_photo(workout_id, jpeg(400, 300)).json()["workout"]["photo_url"]
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    forged = f"{parsed.path}?exp={params['exp'][0]}&sig={'0' * 64}"
    assert fetch(rafael.client, forged).status_code == 404

    real_time = time.time
    monkeypatch.setattr(time, "time", lambda: real_time() + 3600)  # an hour later
    assert fetch(rafael.client, url).status_code == 404


def test_invalid_uploads(rafael, ana, clock):
    workout_id = rafael.checkin().json()["workout"]["id"]
    not_image = rafael.upload_photo(workout_id, b"isso nao e uma imagem", "nota.txt")
    assert not_image.status_code == 422 and not_image.json()["detail"]["code"] == "invalid_photo"
    too_big = rafael.upload_photo(workout_id, b"0" * (8 * 1024 * 1024 + 1))
    assert too_big.status_code == 413
    assert ana.upload_photo(workout_id, jpeg(200, 200)).status_code == 403  # not her workout
    clock.advance(2)
    assert rafael.upload_photo(workout_id, jpeg(200, 200)).json()["detail"]["code"] == "too_old"


def test_photo_bonus_follows_rule_changes(rafael, ana):
    workout_id = rafael.checkin(minutes=30).json()["workout"]["id"]
    rafael.upload_photo(workout_id, jpeg(300, 300))
    values = {"minutes_per_point": 3, "intensity_adjust": 5, "photo_bonus": 10, "week_winner_bonus": 20}
    proposal_id = rafael.post("/rules/proposals", values).json()["pending"]["id"]
    ana.post(f"/rules/proposals/{proposal_id}/approve")
    assert rafael.get("/workouts").json()[0]["points"] == 20  # 10 + new photo bonus


def test_deleting_the_workout_removes_the_photo(rafael, tmp_path):
    workout_id = rafael.checkin().json()["workout"]["id"]
    rafael.upload_photo(workout_id, jpeg(300, 300))
    assert len(list((tmp_path / "photos").rglob("*.jpg"))) == 1
    assert rafael.delete(f"/workouts/{workout_id}").status_code == 204
    assert list((tmp_path / "photos").rglob("*.jpg")) == []


def test_cheer_notifies_the_duo(rafael, ana):
    workout_id = ana.checkin(type="Funcional").json()["workout"]["id"]
    assert rafael.post(f"/workouts/{workout_id}/cheer").status_code == 204
    assert ana.notifications() == ["Rafael mandou parabéns pelo seu treino de funcional!"]
    assert ana.post(f"/workouts/{workout_id}/cheer").status_code == 403


def test_s3_storage_uses_private_objects_and_presigned_urls():
    calls = []

    class FakeClient:
        def put_object(self, **kwargs):
            calls.append(("put", kwargs["Bucket"], kwargs["Key"]))

        def delete_object(self, **kwargs):
            calls.append(("delete", kwargs["Bucket"], kwargs["Key"]))

        def generate_presigned_url(self, operation, Params, ExpiresIn):  # noqa: N803 (boto3 names)
            return f"https://s3.example/{Params['Bucket']}/{Params['Key']}?expires={ExpiresIn}"

    storage = S3Storage.__new__(S3Storage)
    storage.bucket, storage.ttl_seconds, storage.client = "gym-duel", 600, FakeClient()
    storage.save("workouts/1.jpg", b"jpg")
    storage.delete("workouts/1.jpg")
    assert calls == [("put", "gym-duel", "workouts/1.jpg"), ("delete", "gym-duel", "workouts/1.jpg")]
    assert storage.signed_url("workouts/1.jpg") == "https://s3.example/gym-duel/workouts/1.jpg?expires=600"
