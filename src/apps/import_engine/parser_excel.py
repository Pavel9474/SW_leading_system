import re
import pandas as pd


class ExcelStaffParser:
    """Парсер файлов штатного расписания (.xlsx или .csv) для импорта сотрудников и оргструктуры."""

    EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

    def __init__(self, file_path_or_buffer):
        self.file = file_path_or_buffer

    def parse(self) -> tuple[list[dict], list[dict]]:
        """Парсит файл и возвращает кортеж: (список валидных строк, список ошибок)."""
        if isinstance(self.file, str) and self.file.endswith('.csv'):
            df = pd.read_csv(self.file)
        else:
            df = pd.read_excel(self.file)

        valid_rows = []
        errors = []

        for idx, row in df.iterrows():
            row_num = idx + 2  # Учет строки заголовка (Excel 1-based)

            # Извлечение ФИО
            fio = str(row.get('ФИО сотрудника', row.get('ФИО', ''))).strip()
            if not fio or fio.lower() in ['nan', 'none', 'вакансия']:
                continue

            # Извлечение Email с проверкой по регулярному выражению
            email = str(row.get('Электронная почта / Email', row.get('Email', row.get('email', '')))).strip()
            if not email or email.lower() == 'nan':
                errors.append({"row": row_num, "error": f"Отсутствует email для сотрудника: {fio}"})
                continue

            if not self.EMAIL_REGEX.match(email):
                errors.append({"row": row_num, "error": f"Некорректный формат Email: {email}"})
                continue

            # Извлечение Логина
            login = str(row.get('Логин / Username', row.get('Username', row.get('login', '')))).strip()
            if not login or login.lower() == 'nan':
                login = email.split('@')[0]

            # Иерархия подразделений (разбор по символу '/')
            dept_raw = str(row.get('Наименование подразделения', row.get('Структурное подразделение', 'Общий отдел'))).strip()
            if not dept_raw or dept_raw.lower() == 'nan':
                dept_raw = 'Общий отдел'
            dept_hierarchy = [d.strip() for d in dept_raw.split('/') if d.strip()]

            # Наименование должности
            position_name = str(row.get('Наименование должности', row.get('Должность', 'Сотрудник'))).strip()
            if not position_name or position_name.lower() == 'nan':
                position_name = 'Сотрудник'

            # Признак основного места работы
            is_primary_raw = str(row.get('Признак основного места работы', row.get('Основное место', 'Да'))).strip()
            is_primary = is_primary_raw.lower() in ['да', 'true', '1', 'основное', 'yes', 'основная']

            # Разбор ФИО на Фамилию, Имя, Отчество
            fio_parts = fio.split()
            last_name = fio_parts[0] if len(fio_parts) > 0 else ''
            first_name = fio_parts[1] if len(fio_parts) > 1 else ''
            middle_name = fio_parts[2] if len(fio_parts) > 2 else None

            valid_rows.append({
                "row_number": row_num,
                "last_name": last_name,
                "first_name": first_name,
                "middle_name": middle_name,
                "login": login,
                "email": email,
                "departments": dept_hierarchy,
                "position": position_name,
                "is_primary": is_primary
            })

        return valid_rows, errors