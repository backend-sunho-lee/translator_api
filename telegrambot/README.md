# 텔레그램봇

## 우리의 텔레그램봇

### 번역봇
번역기 돌린 결과를 알려주는 봇

@langchainbot


### 트레이너봇
사용자가 번역을 기여하는 봇

@langchainbottrainer




## 구조

```
boilerplate
├─ actions.py
├─ bot_translation.py
└─ bot_trainer.py
```

봇의 기본틀을 Class로 만든다. = TelegramBot

TelegramBot 클래스를 오버라이딩과 오버로딩을 적절히 섞어 각 봇의 특징에 맞게 개조하기




## 주의할 스펙

- python 3.5+
- async
