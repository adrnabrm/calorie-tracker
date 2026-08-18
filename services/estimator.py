# Gemini fallback: estimate nutrition when USDA lookup fails (flags result as "estimated")
#
# SDK: from google import genai
# Client: genai.Client()
# Call: client.interactions.create(
#     model="gemini-3.1-flash-lite",
#     input=<text prompt with food name>,
#     response_format={"type": "text", "mime_type": "application/json", "schema": <schema>},
# )
