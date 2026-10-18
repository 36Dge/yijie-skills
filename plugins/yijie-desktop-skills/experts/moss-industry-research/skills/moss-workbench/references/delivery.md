# 冻结与文件交付
research_state包含唯一研究范围、来源、计算和研究结论。freeze实际计算并哈希整个payload；deliver重新计算核对冻结哈希，以统一content blocks生成格式；verify核对当前state、计算和每个文件hash。不接收模型写入的validation=pass作为证据，不将文件存在/扩展名视为完成。事实语义仍须对照原文审阅。

HTML：真实离线章节链接、文本筛选、键盘焦点；无CDN/外部图像。使用`python3 -B scripts/preview.py --project <delivery>`可前台预览，只提供receipt匹配的四静态文件、loopback/CSP；正常stdin stop关闭，不后台常驻。
XLSX：自有OOXML，原始Facts与Metrics数字表、完整叙事章节、来源与版本；是冻结值表而非可编辑输入自动重算模型。更新须改state后重新freeze/deliver，不能改单元格还保留原receipt。
DOCX：自有可编辑段落和标题，正文/来源/限制完整；系统Word/WPS实际打开与渲染。
PPTX：自有可编辑简报，长文本分页、不截断，统一内容/引用/限制，无缺失上游模板。为完整证据简报，不承诺品牌模板或上游图表库。
PDF：正常LibreOffice将同一DOCX转换，实际CLI成功和文件检查才登记；依赖路径/摘要记录。未指定或不可用时先报缺依赖；生成异常保留部分文件，不伪造成功、不强杀。无需PDF的任务不启动Office。正常独立profile仅隔离本次转换的配置，不拦截系统调用。生成的PDF与DOCX必须逐页渲染查看，不把转换成功当视觉通过。

文件由Finder/系统应用打开；当前易界聊天链接惰性，不声称一键打开/自动Artifact登记。回执只标generated-and-hashed，视觉和语义分别检查。截图/QA报告为验收证据，不回写原产物。默认只HTML，PDF内部DOCX为转换源而非额外交付承诺。没有内置定时监控、自动跨专家转发或团队。

本机macOS转换使用系统Heiti SC中文字体及正常FONTCONFIG_FILE字体目录声明，缓存仅在本次输出profile；不安装/替换字体，不修改全局配置，不拦截运行时。其他机器仍须核对中文字体与转换版本；字体摘要进入回执。
