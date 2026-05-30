# Demo Data Ideas

The `raw_example/demo_germany_energy_data` dataset is a compact data library for testing Loom data discovery, source review, and small downstream analyses.

## Ideas

- Build a 24-hour German electricity data visualization demo.
  做一个 24 小时德国电力数据可视化 demo。

- Compute residual load from German load, wind, and solar data.
  用德国负荷、风电和光伏数据计算剩余负荷。

- Check the 2015 German capacity margin against peak residual load.
  用 2015 年德国装机容量检查峰值剩余负荷下的容量裕度。

- Show how an agent detects and documents missing solar values.
  展示 agent 如何发现并记录光伏数据缺失值。

- Generate a short data-source audit report from Loom cards and raw files.
  基于 Loom 卡片和原始文件生成一份简短的数据来源审计报告。

- Compare the 2015 hourly power slice with 2024 German electricity context.
  将 2015 年小时电力切片与 2024 年德国电力背景数据进行对照。

- Summarize German 2030, 2040, and 2045 climate targets for model context.
  总结德国 2030、2040 和 2045 年气候目标，作为建模背景。

- Demonstrate that raw data is a library, not model configuration.
  演示原始数据是数据图书馆，而不是模型配置。

- Create a tiny single-country power-balance notebook outside `raw_data`.
  在 `raw_data` 外创建一个小型单国家电力平衡 notebook。

- Build a from-scratch pandas model that calculates residual load and capacity margin.
  从头用 pandas 建一个计算剩余负荷和容量裕度的小模型。

- Build a tiny PyPSA single-bus Germany optimal dispatch model from the OPSD load, wind, solar, and capacity data.
  建一个 PyPSA 德国单母线最优调度模型。

- Test whether Loom lookup finds nested source notes before raw CSV files.
  测试 Loom 查询是否会先找到嵌套来源批注，再定位原始 CSV 文件。
