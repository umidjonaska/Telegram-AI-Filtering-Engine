import requests
from config import HF_ACCESS_TOKEN

HF_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"

HF_API_URL = "https://router.huggingface.co/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {HF_ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

def is_important(text: str) -> bool:
    try:
        response = requests.post(
            HF_API_URL,
            headers=headers,
            json={
                "model": HF_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "Siz Telegram xabarlarini filter qiluvchi AI siz. Faqat YES yoki NO deb javob bering."
                    },
                    {
                        "role": "user",
                        "content": f"""
                                Agar xabar ish taklifi, freelance, IT, backend yoki Germaniyada ish bilan bog‘liq bo‘lsa YES deb javob ber.
                                Aks holda NO deb javob ber.

                                Xabar: {text}
                                """
                    }
                ],
                "max_tokens": 5,
                "temperature": 0
            },
            timeout=30
        )

        if response.status_code != 200:
            print("HF API error:", response.text)
            return False

        data = response.json()
        result = data["choices"][0]["message"]["content"].strip().upper()

        return result.startswith("YES")

    except Exception as e:
        print("HF request error:", e)
        return False
