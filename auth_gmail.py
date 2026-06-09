import pickle
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/gmail.send']
flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)

# Явно указываем redirect_uri для ручного ввода
flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'

auth_url, _ = flow.authorization_url(prompt='consent')

print("\n" + "="*60)
print("🔐 ПЕРЕЙДИТЕ ПО ЭТОЙ ССЫЛКЕ В БРАУЗЕРЕ:")
print("="*60)
print(auth_url)
print("="*60)
print("\n📋 ПОСЛЕ РАЗРЕШЕНИЯ ДОСТУПА:")
print("   Вы получите код на отдельной странице")
print("   Скопируйте его и вставьте сюда\n")

code = input("✏️ Вставьте код сюда: ").strip()

flow.fetch_token(code=code)

with open('token.pickle', 'wb') as token:
    pickle.dump(flow.credentials, token)

print("\n✅ Токен успешно сохранён в token.pickle!")
