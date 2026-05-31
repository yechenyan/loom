export type ExploreWorkspace = {
  name: string;
  dataset_count: number;
  readme_markdown: string;
  datasets: ExploreDataset[];
};

export type ExploreDataset = {
  name: string;
  path: string;
  overview_markdown: string;
  source: ExploreSource;
  csv_count: number;
  total_row_count: number;
  csv_files: ExploreCsvFile[];
  csv_profiles: ExploreCsvProfile[];
};

export type ExploreSource = {
  url?: string;
  summary?: string;
  license?: string;
  notes?: string;
  key_sites?: string[];
};

export type ExploreCsvFile = {
  file_name: string;
  dataset_relative_path?: string;
  row_count: number;
  file_size_bytes: number;
  column_count: number;
  columns: string[];
  summary?: string;
  card_file?: string;
  profile_file?: string;
  column_roles?: Record<string, string>;
};

export type ExploreCsvProfile = {
  file_name: string;
  dataset_relative_path?: string;
  row_count: number;
  file_size_bytes: number;
  columns: ExploreColumnProfile[];
  head?: Record<string, string>[];
  tail?: Record<string, string>[];
  notes?: string[];
};

export type ExploreColumnProfile = {
  name: string;
  non_empty_count: number;
  empty_count: number;
  type_counts: Record<string, number>;
  top_values?: { value: string; count: number }[];
  numeric_stats?: {
    count: number;
    min: number;
    max: number;
    mean: number;
  };
};

export type RawManifest = Record<string, { sha256: string; size_bytes: number }>;
