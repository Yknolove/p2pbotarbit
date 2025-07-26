import os, openai, subprocess, sys

openai.api_key = os.getenv("OPENAI_API_KEY")

# 1) Собираем дифф всех .py файлов в репо
diff = subprocess.check_output(["git", "diff", "main", "--", "*.py"]).decode()
if not diff.strip():
    print("No changes to review.")
    sys.exit(0)

# 2) Отправляем его ChatGPT с запросом “zapatch” 
resp = openai.ChatCompletion.create(
    model="gpt-4o-mini",
    messages=[
      {"role":"system","content":"Ты — AI-разработчик, который возвращает только unified diff."},
      {"role":"user","content":f"Есть этот diff:\n```\n{diff}\n```\nПожалуйста, сгенерируй патч, фиксируя все проблемы и обновляя импорты aiogram, добавь базовый логгер и убери любые ошибки."}
    ],
    temperature=0.0,
)
patch = resp.choices[0].message.content

# 3) Применяем полученный патч
proc = subprocess.run(["git", "apply"], input=patch.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
if proc.returncode != 0:
    print("Failed to apply patch:", proc.stderr.decode())
    sys.exit(1)

print("Patch applied successfully.")
