import re

text = '@paycollect_bot 01.01.2024 - Объект2 - Стройка МСК - Этап 3 - Оплата за окна - Оплата за окна алюминий - 3.500 - ООО Петрович - ООО Дом Газобетон'
if text.startswith('@paycollect_bot'):
    text = text.lstrip('@paycollect_bot').strip()
    text = [item.strip() for item in text.split('-')]
    errors = []  # Список для хранения сообщений об ошибках

    # Проверяем каждую часть текста с помощью регулярных выражений
    if not re.match(r"\d{2}\.\d{2}\.\d{4}", text[0]):  # Проверяем дату
        errors.append('Ошибка в дате')
    if not re.match(r"[\w\s.,*-]+", text[1]):  # Проверяем название объекта
        errors.append('Ошибка в названии объекта')
    if not re.match(r"[\w\s]+", text[2]):  # Проверяем регион
        errors.append('Ошибка в регионе')
    if not re.match(r"[\w\s]+", text[3]):  # Проверяем этап/вид расходов
        errors.append('Ошибка в категории этапе/виде расходов')
    if not re.match(r"[\w\s]+", text[4]):  # Проверяем описание
        errors.append('Ошибка в описании')
    if not re.match(r"[\w\s.,*-]+", text[5]):  # Проверяем детализацию расходов
        errors.append('Ошибка в детализации расходов')
    if not re.match(r"^\d+$", text[6]):
        errors.append('Ошибка в сумме: некорректный формат (только цифры)') # Проверяем сумму (amount) - только цифры, никаких других символов
    if not re.match(r"[\w\s.,*-]+", text[7]):  # Проверяем поставщика
        errors.append('Ошибка в поставщике')
    if not re.match(r"[\w\s]+", text[8]):  # Проверяем компанию
        errors.append('Ошибка в компании')

    # Выводим ошибки, если они есть
    if errors:
        for error in errors:
            print(error)
    else:
        date, project, direction, stage, category, description, amount, supplier, company = tuple(text)
        row = [
                        date, project.strip().title(), '', direction.strip().title(), stage, category.strip(), description.strip(), amount,
                        supplier.strip(), f"https://t.me/c/2890383045/1", company.strip()]

        print(row)