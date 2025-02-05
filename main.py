import os
import hashlib
import datetime
import sys
import time
import asyncio

# Глобальные переменные для отслеживания прогресса
processed_files = 0
total_files = 0


def format_file_size(size):
    """
    Форматирует размер файла в удобочитаемый вид (Bytes, KB, MB или GB).
    """
    if size >= 1 << 30:  # 1 GB
        return f"{size / (1 << 30):.2f} GB"
    elif size >= 1 << 20:  # 1 MB
        return f"{size / (1 << 20):.2f} MB"
    elif size >= 1 << 10:  # 1 KB
        return f"{size / (1 << 10):.2f} KB"
    else:
        return f"{size} Bytes"


def get_file_sha1(filepath):
    """
    Вычисляет SHA-1 хеш файла.
    При ошибке доступа возвращает сообщение.
    """
    try:
        hash_sha1 = hashlib.sha1()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha1.update(chunk)
        return hash_sha1.hexdigest()
    except Exception:
        return "Ошибка доступа"


def count_files(path):
    """
    Рекурсивно подсчитывает количество файлов в каталоге.
    """
    count = 0
    try:
        entries = os.listdir(path)
    except Exception:
        return 0
    for entry in entries:
        full_path = os.path.join(path, entry)
        if os.path.isdir(full_path):
            count += count_files(full_path)
        else:
            count += 1
    return count


async def process_path(path):
    """
    Асинхронно получает атрибуты файла или каталога по заданному пути.
    Для каталога – рекурсивно обходит всех детей (сначала каталоги, затем файлы).
    Для файла – получает дату создания, размер и SHA-1.
    """
    loop = asyncio.get_event_loop()
    try:
        stat_result = await loop.run_in_executor(None, os.stat, path)
    except Exception:
        return None

    creation_time = datetime.datetime.fromtimestamp(stat_result.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
    if os.path.isdir(path):
        # Обработка каталога
        try:
            entries = await loop.run_in_executor(None, os.listdir, path)
        except Exception:
            entries = []
        # Разделяем на каталоги и файлы
        dirs = []
        files = []
        for entry in entries:
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                dirs.append(entry)
            else:
                files.append(entry)

        # Сортировка по имени (без учета регистра) и дате создания
        def sort_key(entry):
            full = os.path.join(path, entry)
            try:
                st = os.stat(full)
                return (entry.lower(), st.st_ctime)
            except Exception:
                return (entry.lower(), 0)

        dirs = sorted(dirs, key=sort_key)
        files = sorted(files, key=sort_key)
        children = []
        # Сначала каталоги
        for entry in dirs:
            full_path = os.path.join(path, entry)
            child = await process_path(full_path)
            if child is not None:
                children.append(child)
        # Затем файлы (параллельно)
        file_tasks = []
        for entry in files:
            full_path = os.path.join(path, entry)
            file_tasks.append(process_path(full_path))
        file_results = await asyncio.gather(*file_tasks)
        for res in file_results:
            if res is not None:
                children.append(res)
        return {
            'type': 'dir',
            'name': os.path.basename(path),
            'path': path,
            'creation_time': creation_time,
            'children': children
        }
    else:
        # Обработка файла
        try:
            size_val = await loop.run_in_executor(None, os.path.getsize, path)
            size_formatted = format_file_size(size_val)
        except Exception:
            size_formatted = "Н/Д"
        sha1_val = await loop.run_in_executor(None, get_file_sha1, path)
        global processed_files
        processed_files += 1
        sys.stdout.write(f"\rОбработано файлов: {processed_files}/{total_files}")
        sys.stdout.flush()
        return {
            'type': 'file',
            'name': os.path.basename(path),
            'path': path,
            'creation_time': creation_time,
            'size': size_formatted,
            'sha1': sha1_val
        }


# Функция для преобразования дерева в плоский список строк таблицы
row_counter = 1


def flatten_tree(node, parent_id=None, level=0):
    """
    Рекурсивно преобразует узел дерева (словарь) в список строк <tr> для таблицы.
    Каждая строка получает уникальный id (data-tt-id) и, если является дочерней, атрибут data-tt-parent-id.
    Дополнительно в строку записываются data-атрибуты для сортировки.
    """
    global row_counter
    rows = []
    current_id = row_counter
    row_counter += 1

    data_name = node['name']
    data_date = node['creation_time']
    if node['type'] == 'dir':
        data_size = ""
        data_sha1 = ""
    else:
        data_size = node.get('size', "")
        data_sha1 = node.get('sha1', "")

    # Визуальный отступ для столбца "Name"
    indent = "&nbsp;" * (level * 4)
    if node['type'] == 'dir':
        # Оборачиваем значок и имя папки в один элемент с классом directory-name,
        # чтобы по нему можно было кликнуть для переключения раскрытия
        display_name = f"<span class='directory-name' style='cursor: pointer;'>&#128193; {indent}{data_name}</span>"
    else:
        display_name = f"{indent}{data_name}"

    if node['type'] == 'file':
        # Создаем контейнер flex: слева текст SHA-1, справа кнопка для копирования
        sha1_cell = (
            f"""<div style="display: flex; justify-content: space-between; align-items: center;">"""
            f"""<span class="sha1" data-sha1="{data_sha1}">SHA-1: {data_sha1}</span>"""
            f"""<button class="copy-btn btn btn-sm btn-outline-secondary">Copy SHA-1</button>"""
            f"""</div>"""
        )
    else:
        sha1_cell = ""

    parent_attr = f' data-tt-parent-id="{parent_id}"' if parent_id is not None else ""
    row = f"""<tr data-tt-id="{current_id}"{parent_attr} data-name="{data_name}" data-date="{data_date}" data-size="{data_size}" data-sha1="{data_sha1}">
  <td>{display_name}</td>
  <td>{data_date}</td>
  <td>{data_size}</td>
  <td>{sha1_cell}</td>
</tr>"""
    rows.append(row)
    if node['type'] == 'dir' and 'children' in node:
        for child in node['children']:
            rows.extend(flatten_tree(child, parent_id=current_id, level=level + 1))
    return rows


def main():
    global total_files
    # Задайте путь к каталогу и имя выходного HTML‑файла
    directory = r"C:\Users\User\AppData\Local\BeamNG.drive\0.34"
    output_file = r"C:\Users\User\Desktop\DirectoryStructure.html"

    if not os.path.exists(directory):
        print("Ошибка: Директория не найдена.")
        return

    print("Подсчет файлов в каталоге...")
    total_files = count_files(directory)
    print(f"Найдено файлов: {total_files}")

    start_time = time.time()
    # Асинхронное сканирование директории
    tree = asyncio.run(process_path(directory))
    # Для таблицы будем отображать содержимое корневой директории
    table_rows = []
    if tree and 'children' in tree:
        for child in tree['children']:
            table_rows.extend(flatten_tree(child))
    table_body = "\n".join(table_rows)
    print()  # переход на новую строку после показа прогресса

    # Формирование HTML‑страницы с табличным представлением, плагином treeTable и сортировкой
    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <title>Directory Structure</title>
  <meta charset="UTF-8">
  <!-- Bootstrap CSS -->
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
  <!-- jQuery -->
  <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
  <!-- jQuery treetable CSS и JS -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/jquery-treetable/3.2.0/jquery.treetable.css" />
  <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery-treetable/3.2.0/jquery.treetable.min.js"></script>
  <style>
    body {{
      font-family: Arial, sans-serif;
    }}
    table {{
      width: 100%;
    }}
    th {{
      cursor: pointer;
    }}
  </style>
</head>
<body class="container my-4">
  <h1 class="mb-4">Directory Structure: {directory}</h1>
  <table id="tree-table" class="table table-bordered">
    <thead>
      <tr>
        <th onclick="sortColumn('name')">Name</th>
        <th onclick="sortColumn('date')">Creation Time</th>
        <th onclick="sortColumn('size')">Size</th>
        <th onclick="sortColumn('sha1')">SHA-1</th>
      </tr>
    </thead>
    <tbody>
      {table_body}
    </tbody>
  </table>

  <script>
    // Глобальный объект для отслеживания порядка сортировки по каждому столбцу
    var sortOrder = {{
      name: "asc",
      date: "asc",
      size: "asc",
      sha1: "asc"
    }};

    function sortColumn(column) {{
      // Переключаем порядок сортировки для выбранного столбца
      sortOrder[column] = sortOrder[column] === "asc" ? "desc" : "asc";
      sortTree(column, sortOrder[column]);
    }}

    function sortTree(column, order) {{
      function sortChildren(parentId) {{
        var rows;
        if (parentId === null) {{
          // Строки верхнего уровня (без data-tt-parent-id)
          rows = $("#tree-table tbody tr").filter(function() {{
            return !$(this).attr("data-tt-parent-id");
          }});
        }} else {{
          rows = $("#tree-table tbody tr").filter(function() {{
            return $(this).attr("data-tt-parent-id") == parentId;
          }});
        }}
        rows = rows.get();
        rows.sort(function(a, b) {{
          var aVal = $(a).data(column);
          var bVal = $(b).data(column);
          if (column === "size") {{
            aVal = parseSize(aVal);
            bVal = parseSize(bVal);
          }}
          if(aVal < bVal) return order === "asc" ? -1 : 1;
          if(aVal > bVal) return order === "asc" ? 1 : -1;
          return 0;
        }});
        $.each(rows, function(index, row) {{
          var rowId = $(row).attr("data-tt-id");
          // Рекурсивно сортируем потомков
          sortChildren(rowId);
          var node = $("#tree-table").treetable("node", rowId);
          if (node && node.$el) {{
              node.$el.detach().appendTo($("#tree-table tbody"));
          }} else {{
              $(row).detach().appendTo($("#tree-table tbody"));
          }}
        }});
      }}

      function parseSize(sizeStr) {{
        if (!sizeStr) return 0;
        var parts = sizeStr.split(" ");
        if(parts.length < 2) return parseFloat(parts[0]) || 0;
        var num = parseFloat(parts[0]);
        var unit = parts[1].toUpperCase();
        if(unit.indexOf("GB") !== -1) return num * 1024 * 1024 * 1024;
        if(unit.indexOf("MB") !== -1) return num * 1024 * 1024;
        if(unit.indexOf("KB") !== -1) return num * 1024;
        return num;
      }}

      sortChildren(null);
    }}

    $(document).ready(function() {{
      $("#tree-table").treetable({{ expandable: true }});

      // Обработка клика по кнопке Copy SHA-1
      $("#tree-table").on("click", ".copy-btn", function(e) {{
        e.stopPropagation();
        var btn = $(this);
        var sha1Text = btn.closest("td").find(".sha1").data("sha1");
        navigator.clipboard.writeText(sha1Text).then(function() {{
          btn.text("Copied!");
          setTimeout(function() {{
            btn.text("Copy SHA-1");
          }}, 1500);
        }});
      }});

      // Обработка клика по элементу с классом directory-name:
      // по клику на значок или имя папки происходит переключение раскрытия
      $("#tree-table").on("click", ".directory-name", function(e) {{
        e.stopPropagation();
        var $row = $(this).closest("tr");
        var nodeId = $row.data("ttId");
        var node = $("#tree-table").treetable("node", nodeId);
        if (node.expanded) {{
          $("#tree-table").treetable("collapseNode", nodeId);
        }} else {{
          $("#tree-table").treetable("expandNode", nodeId);
        }}
      }});
    }});
  </script>
</body>
</html>
"""

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        elapsed_time = time.time() - start_time
        print(f"\nHTML файл создан: {output_file}")
        print(f"Скрипт выполнен за {elapsed_time:.2f} секунд")
    except Exception as e:
        print("Ошибка при записи файла:", e)


if __name__ == "__main__":
    main()
