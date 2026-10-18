# 文件执行与验收
Node18+与Python3.10+标准运行时，ECharts分发库已随受管资源固定；无npm/pnpm安装、CDN、浏览器下载或网络请求。HTML内部CSP关闭连接；不修改易界应用CSP。
1. 实际读用户CSV/JSON与列名。优先直接传原数据文件，不手抄大数组。XLSX需当前已授权且实际可用的读取工具转换为新CSV/JSON，保留原表/行数/映射；不可读则请求CSV，不执行工作簿宏/外链。
2. 参照 ../examples/report-config.json，写明确的配置，不从预置样例挪用数字。
3. 在当前任务工作目录运行：
`node <包根>/scripts/build_report.cjs --config <配置.json> --data <用户数据.csv或json> --output-dir <不存在的新子目录>`
4. exit0及status=complete才说明文件生成。读取validation.json并独立核对input_rows、series、每列sum/missing；data.json须与原数据逐行一致。脚本统计记录是生成依据，不是独立验收通过证书。
5. 用当前可用的正常浏览器/预览工具打开report.html；核对每页有图、图例可切换、悬停值/完整表格正确。无可用预览时如实标记尚未视觉验证，不能说已检查。chart-N.svg是实际ECharts SSR输出，可独立打开，字体采用系统中文回退。
6. 文件路径必须真实存在，旧输出不覆盖。只交付HTML/SVG；PNG若要求且当前没有合法渲染器，说明缺项，不假装格式转换成功。

修复版在写出文件前调用Python标准库独立解析每张SVG；解析失败必须停止，不用文件存在或正则匹配代替可打开验证。字体栈不含嵌套引号，避免破坏SVG style属性。浏览器预览未执行时明确区分结构/数值/XML通过与浏览器交互未验。
