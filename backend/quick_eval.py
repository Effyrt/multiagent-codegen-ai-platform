import requests
import time

API = "https://codegen-backend-428108273170.us-central1.run.app"

tests = [
    "binary search algorithm",
    "merge sort implementation", 
    "check if number is prime",
    "reverse a linked list",
    "validate email address"
]

print("🧪 Running Quick Evaluation\n" + "="*50)

results = []
for i, test in enumerate(tests, 1):
    print(f"\n[{i}/{len(tests)}] Testing: {test}")
    
    try:
        r = requests.post(f"{API}/api/v1/generate", json={"description": test, "language": "python"})
        gen_id = r.json()["generation_id"]
        
        time.sleep(25)
        
        status = requests.get(f"{API}/api/v1/status/{gen_id}").json()
        
        if status["status"] == "completed":
            result = status["result"]
            print(f"   ✅ Quality: {result.get('quality_score', 0)}/10")
            print(f"   ⏱️  Time: {result.get('duration', 0):.1f}s")
            results.append(result.get('quality_score', 0))
        else:
            print(f"   ⏳ Still processing...")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

if results:
    print(f"\n{'='*50}")
    print(f"📊 SUMMARY: {len(results)}/{len(tests)} completed")
    print(f"📊 Avg Quality: {sum(results)/len(results):.1f}/10")
    print(f"{'='*50}")
