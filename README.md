# Скрипт для отправки показаний счетчиков через сайт [кабинет-жителя.рф]()

Cпасибо проекту на github https://github.com/ilkarataev/voda.uu.ru_Home_Assistant, но не хватило варианта работы с
когда есть несколько лицевых счетов на одном аккаунте.

## Команды

* Если у вас несколько лицевых счетов, то сначала надо получить id счета, где находятся счетчики и использовать параметр
  -a (--account)

    ```shell
    python cabinet-rf-api.py -u email -p password accounts
    ```

* получить список счетчиков на текущем лицевом счете

    ```shell
    python cabinet-rf-api.py -u zhukov87@gmail.com -p 5bbfac3d meters
    ```

* получить список счетчиков на конкретеном лицевом счете

    ```shell
    python cabinet-rf-api.py -u email -p password -a id meters
    ```

* отправка показаний. Передаются пары номер счетчика и значение(отправляется только целая часть)
    ```shell
    python cabinet-rf-api.py -u email -p password -a id send 123456780 30 0987654321 10
    ```

# Home Assistant

Скопировать `cabinet-rf-api.py` в папку HA сервера `config`

в файле `configuration.yaml` добавить

```yaml
shell_command:
  send_water_meters_values: >-
    python3 cabinet-rf-api.py -u email -p password -a id send
    номер_счетчика1 {{ states("sensor.waterius_11111111_ch0") | int }}
    номер_счетчика2 {{ states("sensor.waterius_11111111_ch1") | int }} 
```

Автоматизация
```yaml
- id: 329eba76-ea48-4c7a-aa2a-f9d6190a7f8e
  triggers:
    - trigger: time
      at: "09:00:00"
  conditions:
    - condition: template
      value_template: "{{ now().day == 25 }}"
  actions:
    - action: shell_command.send_water_meters_values
```