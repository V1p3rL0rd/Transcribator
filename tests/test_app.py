import os
import wave
import struct
import math
import time
from fastapi.testclient import TestClient
from app.main import app

def create_dummy_wav(path: str, duration_sec: float = 1.0):
    sample_rate = 16000
    num_samples = int(sample_rate * duration_sec)
    with wave.open(path, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        for i in range(num_samples):
            # 440 Hz sine tone
            value = int(32767.0 * 0.5 * math.sin(2.0 * math.pi * 440.0 * i / sample_rate))
            data = struct.pack('<h', value)
            wav_file.writeframesraw(data)

def test_full_pipeline():
    client = TestClient(app)
    
    # 1. Health check
    res_health = client.get("/api/health")
    assert res_health.status_code == 200
    data = res_health.json()
    assert data["status"] == "ok"
    print("Health check passed:", data)

    # 2. Models check
    res_models = client.get("/api/models")
    assert res_models.status_code == 200
    models = res_models.json()
    assert len(models) >= 5
    print(f"Models check passed: {len(models)} models available")

    # 3. Create dummy audio and transcribe
    dummy_wav = "test_audio_sample.wav"
    create_dummy_wav(dummy_wav, duration_sec=1.5)
    
    try:
        with open(dummy_wav, "rb") as f:
            res_upload = client.post(
                "/api/transcribe",
                files={"file": ("test_audio_sample.wav", f, "audio/wav")},
                data={"model_size": "tiny", "language": "en", "task": "transcribe"}
            )
        assert res_upload.status_code == 200
        upload_data = res_upload.json()
        task_id = upload_data["task_id"]
        print(f"Transcription task created: {task_id}")

        # Poll status
        completed = False
        for _ in range(60):
            res_status = client.get(f"/api/tasks/{task_id}")
            assert res_status.status_code == 200
            status_data = res_status.json()
            status = status_data["status"]
            print(f"Task status: {status}, progress: {status_data.get('progress')}%")
            if status == "completed":
                completed = True
                break
            elif status == "failed":
                raise RuntimeError(f"Task failed with error: {status_data.get('error')}")
            time.sleep(1)

        assert completed, "Task did not complete within timeout"
        
        # Test exports
        for fmt in ["txt", "docx", "srt", "vtt", "json"]:
            res_exp = client.get(f"/api/export/{task_id}/{fmt}")
            assert res_exp.status_code == 200
            print(f"Export format {fmt} returned status 200, length: {len(res_exp.content)} bytes")

        print("End-to-end transcription pipeline test PASSED successfully!")
    finally:
        if os.path.exists(dummy_wav):
            os.remove(dummy_wav)

if __name__ == "__main__":
    test_full_pipeline()
