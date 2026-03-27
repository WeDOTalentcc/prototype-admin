"""
Test script for Gemini Voice-to-Text API

Testa os endpoints /voice/transcribe, /voice/analyze e /voice/interview
usando arquivos de áudio de exemplo.
"""
import requests
import json
from pathlib import Path


BASE_URL = "http://localhost:8000/api/v1"


def test_health():
    """Test voice health endpoint."""
    print("🏥 Testing /voice/health...")
    response = requests.get(f"{BASE_URL}/voice/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
    print()


def test_transcribe(audio_file: str):
    """Test audio transcription."""
    print(f"🎤 Testing /voice/transcribe with {audio_file}...")
    
    if not Path(audio_file).exists():
        print(f"   ❌ File not found: {audio_file}")
        print(f"   💡 Create a test audio file or use your own MP3/WAV file")
        print()
        return
    
    with open(audio_file, "rb") as f:
        files = {"audio": (Path(audio_file).name, f, "audio/mpeg")}
        data = {"language": "pt-BR"}
        
        response = requests.post(
            f"{BASE_URL}/voice/transcribe",
            files=files,
            data=data
        )
    
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Transcription successful!")
        print(f"   📝 Text: {result['transcription'][:200]}...")
        print(f"   📊 Metadata: {json.dumps(result['metadata'], indent=2)}")
    else:
        print(f"   ❌ Error: {response.text}")
    print()


def test_analyze(audio_file: str, analysis_type: str = "sentiment"):
    """Test audio analysis."""
    print(f"📊 Testing /voice/analyze ({analysis_type}) with {audio_file}...")
    
    if not Path(audio_file).exists():
        print(f"   ❌ File not found: {audio_file}")
        print()
        return
    
    with open(audio_file, "rb") as f:
        files = {"audio": (Path(audio_file).name, f, "audio/mpeg")}
        data = {"analysis_type": analysis_type}
        
        response = requests.post(
            f"{BASE_URL}/voice/analyze",
            files=files,
            data=data
        )
    
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Analysis successful!")
        print(f"   💡 Analysis: {result['analysis'][:300]}...")
    else:
        print(f"   ❌ Error: {response.text}")
    print()


def test_interview(audio_file: str):
    """Test interview analysis."""
    print(f"🎯 Testing /voice/interview with {audio_file}...")
    
    if not Path(audio_file).exists():
        print(f"   ❌ File not found: {audio_file}")
        print()
        return
    
    with open(audio_file, "rb") as f:
        files = {"audio": (Path(audio_file).name, f, "audio/mpeg")}
        data = {
            "job_title": "Senior Python Developer",
            "questions": "Conte sobre sua experiência,Qual seu maior projeto,Como você lida com prazos"
        }
        
        response = requests.post(
            f"{BASE_URL}/voice/interview",
            files=files,
            data=data
        )
    
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Interview analysis successful!")
        print(f"   🎯 Analysis: {result['interview_analysis'][:400]}...")
        print(f"   📋 Job: {result['metadata']['job_title']}")
    else:
        print(f"   ❌ Error: {response.text}")
    print()


def main():
    """Run all tests."""
    print("=" * 60)
    print("🚀 Gemini Voice-to-Text API Tests")
    print("=" * 60)
    print()
    
    # Test 1: Health check (always works)
    test_health()
    
    # Test 2-4: Audio tests (requires audio file)
    test_audio_file = "test_audio.mp3"
    
    print("📁 Audio file tests:")
    print(f"   Looking for: {test_audio_file}")
    print(f"   💡 To test transcription, provide an audio file:")
    print(f"      - Record audio on your phone/computer")
    print(f"      - Save as {test_audio_file}")
    print(f"      - Or use any MP3/WAV/M4A file")
    print()
    
    # Attempt tests (will skip if file doesn't exist)
    test_transcribe(test_audio_file)
    test_analyze(test_audio_file, "sentiment")
    test_interview(test_audio_file)
    
    print("=" * 60)
    print("✅ Tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
