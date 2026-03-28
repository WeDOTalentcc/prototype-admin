"""
Test Voice API through Next.js Proxy (Frontend → Backend)

Testa se multipart/form-data funciona corretamente através do proxy.
"""
import requests
import json
from pathlib import Path


# Testar através do Next.js proxy (porta 5000)
# Note: Proxy path is /api/lia/api/v1/... → backend receives /api/v1/...
PROXY_URL = "http://localhost:5000/api/lia/api/v1"
# Backend direto (porta 8000)
DIRECT_URL = "http://localhost:8000/api/v1"


def test_health_through_proxy():
    """Test voice health through Next.js proxy."""
    print("=" * 60)
    print("🏥 Testing /voice/health through Next.js PROXY")
    print("=" * 60)
    
    # Proxy (requires trailing slash)
    proxy_response = requests.get(f"{PROXY_URL}/voice/health/")
    print(f"\n📡 Through Proxy (port 5000):")
    print(f"   Status: {proxy_response.status_code}")
    print(f"   Response: {json.dumps(proxy_response.json(), indent=2)}")
    
    # Direct backend
    direct_response = requests.get(f"{DIRECT_URL}/voice/health")
    print(f"\n🔧 Direct Backend (port 8000):")
    print(f"   Status: {direct_response.status_code}")
    print(f"   Response: {json.dumps(direct_response.json(), indent=2)}")
    
    if proxy_response.status_code == 200 and direct_response.status_code == 200:
        print("\n✅ Health check working both ways!")
    else:
        print("\n❌ Health check failed")
    
    print()


def test_multipart_upload():
    """Test multipart/form-data upload through proxy."""
    print("=" * 60)
    print("🎤 Testing Multipart Upload through Next.js PROXY")
    print("=" * 60)
    
    test_file = "test_audio.mp3"
    
    if not Path(test_file).exists():
        print(f"\n❌ Test file not found: {test_file}")
        print(f"💡 To test multipart uploads:")
        print(f"   1. Record a short audio (10-30 seconds)")
        print(f"   2. Save as {test_file}")
        print(f"   3. Run this script again")
        print()
        return
    
    with open(test_file, "rb") as f:
        files = {"audio": (test_file, f, "audio/mpeg")}
        data = {"language": "pt-BR"}
        
        print(f"\n📤 Uploading {test_file} through proxy...")
        print(f"   URL: {PROXY_URL}/voice/transcribe/")
        
        try:
            response = requests.post(
                f"{PROXY_URL}/voice/transcribe/",
                files=files,
                data=data,
                timeout=60
            )
            
            print(f"\n📊 Response:")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ SUCCESS! Multipart upload works through proxy!")
                print(f"   📝 Transcription: {result.get('transcription', '')[:200]}...")
            else:
                print(f"   ❌ FAIL: {response.status_code}")
                print(f"   Error: {response.text[:500]}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    print()


def main():
    """Run all proxy tests."""
    print("\n" + "=" * 60)
    print("🚀 Voice API Proxy Tests (Next.js → FastAPI)")
    print("=" * 60)
    print()
    
    # Test 1: Health check (GET request)
    test_health_through_proxy()
    
    # Test 2: Multipart upload (POST request with files)
    test_multipart_upload()
    
    print("=" * 60)
    print("✅ Proxy tests completed!")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
