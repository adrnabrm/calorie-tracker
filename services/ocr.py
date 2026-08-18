# Gemini vision: extract nutrition facts from a label photo
#
# SDK: from google import genai
# Client: genai.Client()
# Call: client.interactions.create(
#     model="gemini-3.1-flash-lite",
#     input=[
#         {"type": "text", "text": <prompt>},
#         {"type": "image", "data": <base64_str>, "mime_type": "image/jpeg"},
#     ],
#     response_format={"type": "text", "mime_type": "application/json", "schema": <schema>},
# )
