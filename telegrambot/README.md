# 텔레그램봇

## 우리의 텔레그램봇

- 번역봇
번역기 돌린 결과를 알려주는 봇

[@langchainbot](https://t.me/langchainbot)


- 트레이너봇
사용자가 번역을 기여하는 봇

[@langchainbottrainer](https://t.me/LangChainTrainerbot)




## 구조

```
telegrambot
├─ actions.py
├─ translationbot.py
├─ trainerbot.py
├─ test_translationbot.py
└─ test_trainerbot.py
```


- actions

봇의 기본틀을 TelegramBot Class로 만든다.

TelegramBot을 적절히 섞어 각 봇의 특징에 맞게 개조하기


- test

현재 한바퀴 돌 때마다 새로운 update_id를 return 한다. 테스트를 하기에 적절한 return 값이 아님.

봇 코드를 수정하는 것보다 다양한 메세지 오브젝트 넣는 방법이 테스트 케이스 작성하기에 더 빠를 것 같음.

그래서 CoroMocGetUpdates의 return_value로 커버해야할 텔레그램 메세지 오브젝트를 넣었습니다.
