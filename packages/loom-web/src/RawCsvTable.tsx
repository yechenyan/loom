import { getSiteCopy } from "./copy";
import { useI18n } from "./i18n";

export function RawCsvTable({ csvText }: { csvText: string }) {
  const { locale } = useI18n();
  const copy = getSiteCopy(locale).rawTable;
  const rows = parseCsv(csvText);
  const headers = rows[0] || [];
  const bodyRows = rows.slice(1);

  if (!headers.length) {
    return <p className="empty-state">{copy.empty}</p>;
  }

  return (
    <div className="raw-table-card">
      <table className="raw-table">
        <thead>
          <tr>
            {headers.map((header, index) => (
              <th key={`${header}-${index}`}>{header || `column_${index + 1}`}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {bodyRows.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {headers.map((_, columnIndex) => (
                <td key={columnIndex}>{row[columnIndex] || ""}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function parseCsv(text: string) {
  const rows: string[][] = [];
  let row: string[] = [];
  let field = "";
  let quoted = false;

  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    const next = text[index + 1];

    if (char === '"' && quoted && next === '"') {
      field += '"';
      index += 1;
      continue;
    }

    if (char === '"') {
      quoted = !quoted;
      continue;
    }

    if (char === "," && !quoted) {
      row.push(field);
      field = "";
      continue;
    }

    if ((char === "\n" || char === "\r") && !quoted) {
      if (char === "\r" && next === "\n") index += 1;
      row.push(field);
      rows.push(row);
      row = [];
      field = "";
      continue;
    }

    field += char;
  }

  if (field || row.length) {
    row.push(field);
    rows.push(row);
  }

  return rows.filter((item) => item.some((cell) => cell !== ""));
}
