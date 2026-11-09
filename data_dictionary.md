# Data dictionary — кейс 2 «Кредитный конвейер»

## Как заполнять

В `applications.csv` 14 колонок. Все нужно описать. Одна строка — образец.
Для каждой колонки укажи: тип, обязательность, ограничение, пример (из CSV), код ошибки (если валидируется), комментарий.

## Образец (не трогать)

|Поле|Тип|Обяз.|Ограничение|Пример|Код ошибки|Комментарий|
|-|-|-|-|-|-|-|
|app\_id|string|да (сервер)|`app\_NNNN`|app\_0001|—|генерируется сервисом|

## Ваша таблица — 13 оставшихся колонок

|Поле|Тип|Обяз.|Ограничение|Пример|Код ошибки|Комментарий|
|-|-|-|-|-|-|-|
|age|integer|да|18-70|32|AGE\_OUT\_OF\_RANGE|Возраст заемщика|
|income|number|да|>0|120000|MISSING\_INCOME / LOW\_INCOME|Ежемесячный доход заемщика|
|employment|string|да|enum: employed, self-employed, student, retirned, unemployed|employed|-|Занятость заемщика|
|family|string|да|enum: married, children, single|married|-|Семейное положение|
|amount|number|да|10000-5000000|500000|AMOUNT\_LIMIT|Запрашиваемая сумма кредита|
|term|integer|да|3-60|24|-|Срок кредита|
|decision|string|нет|enum: APPROVED, REFUSED, NEED\_MORE\_DATA|APPROVED|-|Итоговое решение по одобрению кредита|
|reason|string|нет|enum: AGE\_OUT\_OF\_RANGE, NEED\_MORE\_DATA, MISSING\_INCOME, LOW\_INCOME, HIGH\_DTI, BKI\_DELIMQUENCY, AMOUNT\_LIMIT, LOW\_SCORE, SMEV\_MISMATCH|LOW\_INCOME|-|Причина отказа|
|client\_id|string|да|`cli\\\\\\\\\\\\\\\_NNNN`|cli\_0001|-|Идентификатор клиента|
|passport\_hash|string|да|16 hex-символов|f727a849055f2224|-|Хэш паспортных данных|
|dti|number|да|>=0.5|0.21|HIGH\_DTI|долговая нагрузка|
|bki\_score|integer|да|300-850|720|BKI\_DELINQUENCY|Кредитный скор БКИ|
|smev\_status|string|да|enum: MATCH, MISMATCH, TIMEOUT, NOT\_CALLED|MATCH|SMEV\_MISMATCH|Статус проверки через СМЭВ|

## Критерий приёмки

* \[ ] Все 14 колонок описаны
* \[ ] Для age указан диапазон 18–70 и AGE\_OUT\_OF\_RANGE
* \[ ] Для income — > 0 и MISSING\_INCOME
* \[ ] Для employment — справочник из 5 значений и INVALID\_EMPLOYMENT
* \[ ] Для passport\_hash — только SHA-256, оригинал не хранится
* \[ ] Для dti — формула (аннуитет / доход), порог 0.5
* \[ ] Для bki\_score — диапазон 300–850, < 550 = отказ
* \[ ] Для smev\_status — MATCH / MISMATCH / TIMEOUT / NOT\_CALLED
* \[ ] Комментарий объясняет «зачем поле»

## Подсказки

* employment — enum из 5: employed, self-employed, student, retired, unemployed.
* family — enum из 3: single, married, children.
* decision — enum из 4: APPROVED, REFUSED, NEED\_MORE\_DATA, MANUAL\_REVIEW.
* passport\_hash — 16 hex-символов, не оригинал паспорта.
* dti — число с 2 знаками, от 0 до бесконечности, порог 0.5.

