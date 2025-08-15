# TASK-30B: 詳細依賴分析和影響評估

- **優先級**: 🔴 CRITICAL
- **預計時間**: 6-8 小時
- **關聯組件**: 所有涉及 JSON 的模組
- **父任務**: TASK-30 純 Database 系統重構專案
- **前置條件**: TASK-30A 完成
- **後續任務**: TASK-30C, TASK-30D

---

## 🎯 任務目標

進行全面的代碼依賴分析，精確識別所有 JSON 相關的代碼路徑、數據流和交互關係，為後續的移除工作提供詳細的技術路線圖。

## ✅ 驗收標準

### 依賴映射
- [ ] 生成完整的 JSON 依賴關係圖
- [ ] 識別所有直接和間接的 JSON 引用
- [ ] 分析跨模組的數據流向
- [ ] 標記高風險和低風險的變更點

### 影響評估
- [ ] 評估每個變更的業務影響
- [ ] 量化技術風險等級
- [ ] 估算重構工作量
- [ ] 識別關鍵路徑和依賴順序

### 技術文檔
- [ ] 創建詳細的重構路線圖
- [ ] 生成代碼變更清單
- [ ] 制定測試策略
- [ ] 建立風險緩解計劃

## 📋 詳細執行步驟

### 1️⃣ 代碼掃描和依賴發現 (2-3 小時)

#### 全局 JSON 依賴掃描
```bash
# 創建分析結果目錄
mkdir -p analysis/dependency_analysis/$(date +%Y%m%d_%H%M%S)
ANALYSIS_DIR="analysis/dependency_analysis/$(date +%Y%m%d_%H%M%S)"

# 掃描所有 JSON 相關的直接引用
echo "=== Direct JSON Imports ===" > "$ANALYSIS_DIR/json_dependencies.txt"
rg "import json" --type py -n >> "$ANALYSIS_DIR/json_dependencies.txt"
rg "from json" --type py -n >> "$ANALYSIS_DIR/json_dependencies.txt"

# 掃描 JSON 方法調用
echo -e "\n=== JSON Method Calls ===" >> "$ANALYSIS_DIR/json_dependencies.txt"
rg "json\.(load|loads|dump|dumps)" --type py -n -A 2 -B 2 >> "$ANALYSIS_DIR/json_dependencies.txt"

# 掃描 JSON 文件路徑引用
echo -e "\n=== JSON File References ===" >> "$ANALYSIS_DIR/json_dependencies.txt"
rg "\.json" --type py -n -A 1 -B 1 >> "$ANALYSIS_DIR/json_dependencies.txt"

# 掃描 knowledge.py 相關引用
echo -e "\n=== Knowledge.py References ===" >> "$ANALYSIS_DIR/json_dependencies.txt"
rg "from core\.knowledge" --type py -n >> "$ANALYSIS_DIR/json_dependencies.txt"
rg "import.*knowledge" --type py -n >> "$ANALYSIS_DIR/json_dependencies.txt"
```

#### 深度依賴分析
```python
# 創建依賴分析腳本
cat > analysis/analyze_dependencies.py << 'EOF'
#!/usr/bin/env python3
"""
深度 JSON 依賴分析工具
分析代碼中所有與 JSON 相關的依賴關係
"""

import ast
import os
import json
from pathlib import Path
from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple

class DependencyAnalyzer:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.dependencies = defaultdict(set)
        self.reverse_dependencies = defaultdict(set)
        self.json_related_files = set()
        self.risk_levels = {}
        
    def analyze_file(self, file_path: Path) -> Dict:
        """分析單個 Python 文件的依賴"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            tree = ast.parse(content)
            analysis = {
                'file': str(file_path.relative_to(self.root_dir)),
                'imports': [],
                'json_usage': [],
                'functions': [],
                'classes': [],
                'risk_indicators': []
            }
            
            for node in ast.walk(tree):
                # 分析 import 語句
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        analysis['imports'].append(alias.name)
                        if 'json' in alias.name:
                            analysis['json_usage'].append(f"import {alias.name}")
                            
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        full_name = f"{module}.{alias.name}"
                        analysis['imports'].append(full_name)
                        if 'json' in module or 'json' in alias.name:
                            analysis['json_usage'].append(f"from {module} import {alias.name}")
                
                # 分析函數定義
                elif isinstance(node, ast.FunctionDef):
                    analysis['functions'].append(node.name)
                    
                # 分析類定義
                elif isinstance(node, ast.ClassDef):
                    analysis['classes'].append(node.name)
                    
                # 分析 JSON 方法調用
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute):
                        if isinstance(node.func.value, ast.Name):
                            if node.func.value.id == 'json':
                                method = node.func.attr
                                analysis['json_usage'].append(f"json.{method}()")
                                analysis['risk_indicators'].append(f"Direct JSON call: json.{method}")
                                
            # 檢查文件內容中的 JSON 相關字符串
            if '.json' in content or 'knowledge.json' in content or 'practice_log.json' in content:
                analysis['risk_indicators'].append("JSON file path reference")
                
            if 'legacy_manager' in content:
                analysis['risk_indicators'].append("Legacy manager reference")
                
            if 'fallback' in content.lower() and 'json' in content.lower():
                analysis['risk_indicators'].append("JSON fallback logic")
                
            return analysis
            
        except Exception as e:
            return {
                'file': str(file_path.relative_to(self.root_dir)),
                'error': str(e),
                'risk_indicators': ['Parse error - manual review needed']
            }
    
    def calculate_risk_level(self, analysis: Dict) -> str:
        """計算風險等級"""
        risk_score = 0
        
        # JSON 使用頻率
        risk_score += len(analysis.get('json_usage', [])) * 2
        
        # 風險指標
        risk_indicators = analysis.get('risk_indicators', [])
        risk_score += len(risk_indicators) * 3
        
        # 特殊風險
        for indicator in risk_indicators:
            if 'fallback' in indicator.lower():
                risk_score += 5
            if 'legacy' in indicator.lower():
                risk_score += 4
            if 'Direct JSON call' in indicator:
                risk_score += 3
                
        # 文件重要性（基於路徑）
        file_path = analysis['file']
        if 'core/' in file_path:
            risk_score += 2
        if 'web/' in file_path:
            risk_score += 1
        if 'database' in file_path:
            risk_score += 3
            
        if risk_score >= 10:
            return "🔴 HIGH"
        elif risk_score >= 5:
            return "🟠 MEDIUM"
        elif risk_score > 0:
            return "🟡 LOW"
        else:
            return "🟢 NONE"
    
    def analyze_all_files(self) -> Dict:
        """分析所有 Python 文件"""
        results = {
            'files': [],
            'summary': {
                'total_files': 0,
                'json_related_files': 0,
                'high_risk_files': 0,
                'medium_risk_files': 0,
                'low_risk_files': 0
            },
            'dependencies': {},
            'critical_paths': []
        }
        
        # 掃描所有 Python 文件
        for py_file in self.root_dir.rglob("*.py"):
            if any(skip in str(py_file) for skip in ['.venv', '__pycache__', '.git']):
                continue
                
            analysis = self.analyze_file(py_file)
            risk_level = self.calculate_risk_level(analysis)
            analysis['risk_level'] = risk_level
            
            results['files'].append(analysis)
            results['summary']['total_files'] += 1
            
            if analysis.get('json_usage') or analysis.get('risk_indicators'):
                results['summary']['json_related_files'] += 1
                
                if 'HIGH' in risk_level:
                    results['summary']['high_risk_files'] += 1
                elif 'MEDIUM' in risk_level:
                    results['summary']['medium_risk_files'] += 1
                elif 'LOW' in risk_level:
                    results['summary']['low_risk_files'] += 1
        
        return results
    
    def generate_dependency_graph(self, results: Dict) -> str:
        """生成依賴關係圖"""
        graph = "# JSON 依賴關係圖\n\n"
        graph += "```mermaid\ngraph TD\n"
        
        # 按風險等級分組
        high_risk = [f for f in results['files'] if 'HIGH' in f.get('risk_level', '')]
        medium_risk = [f for f in results['files'] if 'MEDIUM' in f.get('risk_level', '')]
        
        # 添加高風險節點
        for i, file_info in enumerate(high_risk):
            file_name = file_info['file'].replace('/', '_').replace('.py', '')
            graph += f"    {file_name}[{file_info['file']}]\n"
            graph += f"    {file_name} --> JSON_SYSTEM\n"
            
        # 添加中風險節點
        for i, file_info in enumerate(medium_risk):
            file_name = file_info['file'].replace('/', '_').replace('.py', '')
            graph += f"    {file_name}[{file_info['file']}]\n"
            graph += f"    {file_name} --> JSON_SYSTEM\n"
            
        graph += "    JSON_SYSTEM[JSON System]\n"
        graph += "    JSON_SYSTEM --> DATABASE[Database System]\n"
        graph += "```\n"
        
        return graph

def main():
    analyzer = DependencyAnalyzer('.')
    results = analyzer.analyze_all_files()
    
    # 保存詳細分析結果
    with open('analysis/detailed_dependency_analysis.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # 生成摘要報告
    summary = f"""# JSON 依賴分析摘要

## 📊 統計摘要
- 總文件數: {results['summary']['total_files']}
- JSON 相關文件: {results['summary']['json_related_files']}
- 高風險文件: {results['summary']['high_risk_files']}
- 中風險文件: {results['summary']['medium_risk_files']}
- 低風險文件: {results['summary']['low_risk_files']}

## 🔴 高風險文件
"""
    
    high_risk_files = [f for f in results['files'] if 'HIGH' in f.get('risk_level', '')]
    for file_info in high_risk_files:
        summary += f"\n### {file_info['file']}\n"
        summary += f"- **風險等級**: {file_info['risk_level']}\n"
        summary += f"- **JSON 使用**: {len(file_info.get('json_usage', []))}\n"
        summary += f"- **風險指標**: {len(file_info.get('risk_indicators', []))}\n"
        
        if file_info.get('json_usage'):
            summary += "- **JSON 調用**:\n"
            for usage in file_info['json_usage']:
                summary += f"  - {usage}\n"
                
        if file_info.get('risk_indicators'):
            summary += "- **風險因素**:\n"
            for risk in file_info['risk_indicators']:
                summary += f"  - {risk}\n"
    
    # 生成依賴圖
    dependency_graph = analyzer.generate_dependency_graph(results)
    summary += "\n" + dependency_graph
    
    # 保存摘要
    with open('analysis/dependency_analysis_summary.md', 'w') as f:
        f.write(summary)
    
    print("✅ 依賴分析完成！")
    print(f"📁 詳細結果: analysis/detailed_dependency_analysis.json")
    print(f"📄 摘要報告: analysis/dependency_analysis_summary.md")
    print(f"\n📊 快速統計:")
    print(f"   - 高風險文件: {results['summary']['high_risk_files']}")
    print(f"   - 中風險文件: {results['summary']['medium_risk_files']}")
    print(f"   - JSON 相關文件: {results['summary']['json_related_files']}")

if __name__ == "__main__":
    main()
EOF

chmod +x analysis/analyze_dependencies.py
```

#### 執行深度分析
```bash
# 運行依賴分析
cd /Users/chenliangyu/Desktop/linker
python3 analysis/analyze_dependencies.py

# 生成調用鏈分析
echo "=== Function Call Chain Analysis ===" > "$ANALYSIS_DIR/call_chain_analysis.txt"

# 查找所有調用 json.load 的函數
rg "json\.load" --type py -A 5 -B 5 >> "$ANALYSIS_DIR/call_chain_analysis.txt"

# 查找所有調用這些函數的地方
rg "save_mistake|load_knowledge|load_practice" --type py -A 3 -B 3 >> "$ANALYSIS_DIR/call_chain_analysis.txt"
```

### 2️⃣ 業務流程影響分析 (2 小時)

#### 核心業務流程映射
```bash
cat > analysis/business_impact_analysis.py << 'EOF'
#!/usr/bin/env python3
"""
業務流程影響分析
分析 JSON 移除對核心業務功能的影響
"""

import json
from pathlib import Path

class BusinessImpactAnalyzer:
    def __init__(self):
        self.critical_flows = [
            "練習題生成和評分",
            "錯誤分析和保存",
            "知識點管理",
            "複習計劃生成",
            "統計數據查詢",
            "用戶進度追蹤"
        ]
        
        self.api_endpoints = []
        self.data_models = []
        
    def analyze_api_endpoints(self):
        """分析 API 端點的 JSON 依賴"""
        router_files = [
            'web/routers/api_knowledge.py',
            'web/routers/knowledge.py',
            'web/routers/practice.py',
            'web/routers/pages.py',
            'web/routers/calendar.py'
        ]
        
        endpoint_analysis = {}
        
        for router_file in router_files:
            try:
                with open(router_file, 'r') as f:
                    content = f.read()
                
                # 檢查 JSON 相關的端點
                if 'knowledge' in content and ('json' in content.lower() or 'legacy' in content.lower()):
                    endpoint_analysis[router_file] = {
                        'has_json_dependency': True,
                        'risk_level': 'HIGH' if 'legacy' in content else 'MEDIUM',
                        'affected_endpoints': []
                    }
                    
                    # 提取路由定義
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if '@router.' in line and ('get' in line.lower() or 'post' in line.lower()):
                            endpoint_analysis[router_file]['affected_endpoints'].append(line.strip())
                            
            except FileNotFoundError:
                continue
                
        return endpoint_analysis
    
    def analyze_data_flows(self):
        """分析數據流向"""
        data_flows = {
            "用戶提交答案": {
                "entry_point": "POST /api/knowledge/practice",
                "data_path": [
                    "web/routers/practice.py",
                    "core/ai_service.py (grading)",
                    "core/knowledge.py (save_mistake)",
                    "data/knowledge.json (JSON storage)"
                ],
                "database_alternative": [
                    "web/routers/practice.py",
                    "core/ai_service.py (grading)",
                    "core/database/adapter.py (save_mistake_async)",
                    "PostgreSQL database"
                ],
                "migration_complexity": "MEDIUM"
            },
            "獲取複習候選": {
                "entry_point": "GET /api/knowledge/review-candidates",
                "data_path": [
                    "web/routers/api_knowledge.py",
                    "core/knowledge.py (get_review_candidates)",
                    "data/knowledge.json (JSON storage)"
                ],
                "database_alternative": [
                    "web/routers/api_knowledge.py",
                    "core/database/adapter.py (get_review_candidates_async)",
                    "PostgreSQL database"
                ],
                "migration_complexity": "LOW"
            },
            "統計數據查詢": {
                "entry_point": "GET /api/knowledge/statistics",
                "data_path": [
                    "web/routers/api_knowledge.py",
                    "core/knowledge.py (get_statistics)",
                    "data/knowledge.json + data/practice_log.json"
                ],
                "database_alternative": [
                    "web/routers/api_knowledge.py",
                    "core/database/adapter.py (get_statistics_async)",
                    "PostgreSQL aggregated queries"
                ],
                "migration_complexity": "HIGH"
            }
        }
        
        return data_flows
    
    def generate_impact_report(self):
        """生成影響評估報告"""
        api_analysis = self.analyze_api_endpoints()
        data_flows = self.analyze_data_flows()
        
        report = f"""# 業務流程影響分析報告

## 📊 執行摘要

### 關鍵發現
- **高風險端點**: {sum(1 for a in api_analysis.values() if a.get('risk_level') == 'HIGH')}
- **中風險端點**: {sum(1 for a in api_analysis.values() if a.get('risk_level') == 'MEDIUM')}
- **核心數據流**: {len(data_flows)}

### 總體風險評估
- **業務連續性風險**: 🟡 MEDIUM (有完整的資料庫替代方案)
- **數據完整性風險**: 🟢 LOW (完整的備份和驗證機制)
- **性能影響**: 🟢 POSITIVE (資料庫查詢比 JSON 文件讀取更高效)

## 🔍 詳細分析

### API 端點影響
"""
        
        for router_file, analysis in api_analysis.items():
            report += f"\n#### {router_file}\n"
            report += f"- **風險等級**: {analysis.get('risk_level', 'UNKNOWN')}\n"
            report += f"- **JSON 依賴**: {'是' if analysis.get('has_json_dependency') else '否'}\n"
            report += f"- **受影響端點**: {len(analysis.get('affected_endpoints', []))}\n"
            
            if analysis.get('affected_endpoints'):
                report += "- **端點列表**:\n"
                for endpoint in analysis['affected_endpoints']:
                    report += f"  - {endpoint}\n"
        
        report += "\n### 核心數據流分析\n"
        
        for flow_name, flow_info in data_flows.items():
            report += f"\n#### {flow_name}\n"
            report += f"- **入口點**: {flow_info['entry_point']}\n"
            report += f"- **遷移複雜度**: {flow_info['migration_complexity']}\n"
            report += "- **當前路徑**:\n"
            for step in flow_info['data_path']:
                report += f"  1. {step}\n"
            report += "- **目標路徑**:\n"
            for step in flow_info['database_alternative']:
                report += f"  1. {step}\n"
        
        report += """

## 🎯 遷移策略建議

### 階段性遷移
1. **階段 1**: 後端 API 切換（保持前端不變）
2. **階段 2**: 數據源切換（JSON → Database）
3. **階段 3**: 清理舊代碼和文件

### 風險緩解
1. **A/B 測試**: 使用功能開關逐步切換
2. **雙寫策略**: 臨時同時寫入 JSON 和資料庫
3. **監控告警**: 實時監控錯誤率和性能

### 回滾計劃
- 保持 JSON 文件備份
- 保留切換開關
- 自動化回滾腳本
"""
        
        return report

def main():
    analyzer = BusinessImpactAnalyzer()
    report = analyzer.generate_impact_report()
    
    with open('analysis/business_impact_analysis.md', 'w') as f:
        f.write(report)
    
    print("✅ 業務影響分析完成！")
    print("📄 報告位置: analysis/business_impact_analysis.md")

if __name__ == "__main__":
    main()
EOF

chmod +x analysis/business_impact_analysis.py
python3 analysis/business_impact_analysis.py
```

### 3️⃣ 測試影響分析 (1-2 小時)

#### 測試覆蓋度分析
```bash
# 分析現有測試中的 JSON 依賴
echo "=== Test JSON Dependencies ===" > "$ANALYSIS_DIR/test_analysis.txt"

# 掃描測試文件中的 JSON 相關代碼
find tests/ -name "*.py" -exec grep -l "json\|knowledge\.py\|legacy" {} \; >> "$ANALYSIS_DIR/test_files_with_json.txt"

# 分析每個測試文件的依賴
for test_file in $(cat "$ANALYSIS_DIR/test_files_with_json.txt"); do
    echo "=== $test_file ===" >> "$ANALYSIS_DIR/test_analysis.txt"
    grep -n "json\|knowledge\|legacy\|fallback" "$test_file" >> "$ANALYSIS_DIR/test_analysis.txt"
    echo "" >> "$ANALYSIS_DIR/test_analysis.txt"
done

# 運行測試覆蓋率分析
pytest --cov=core --cov=web --cov-report=html --cov-report=term > "$ANALYSIS_DIR/current_test_coverage.txt"
```

#### 創建測試重構計劃
```python
cat > analysis/test_migration_plan.py << 'EOF'
#!/usr/bin/env python3
"""
測試重構計劃生成器
分析現有測試並生成重構策略
"""

import os
import re
from pathlib import Path

class TestMigrationPlanner:
    def __init__(self):
        self.test_files = []
        self.migration_plan = {}
        
    def analyze_test_file(self, file_path: Path):
        """分析單個測試文件"""
        with open(file_path, 'r') as f:
            content = f.read()
        
        analysis = {
            'file': str(file_path),
            'json_dependencies': [],
            'knowledge_imports': [],
            'database_usage': [],
            'migration_complexity': 'LOW',
            'required_changes': []
        }
        
        # 檢查 JSON 依賴
        if 'import json' in content or 'from json' in content:
            analysis['json_dependencies'].append('Direct JSON import')
            analysis['migration_complexity'] = 'MEDIUM'
        
        # 檢查 knowledge.py 引用
        if 'from core.knowledge' in content or 'core.knowledge' in content:
            analysis['knowledge_imports'].append('Legacy knowledge.py import')
            analysis['migration_complexity'] = 'HIGH'
            analysis['required_changes'].append('Replace with DatabaseAdapter')
        
        # 檢查是否已使用資料庫
        if 'DatabaseAdapter' in content or 'asyncpg' in content:
            analysis['database_usage'].append('Already using database')
            analysis['migration_complexity'] = 'LOW'
        
        # 檢查測試 fixtures
        if 'temp_data_dir' in content or 'mock_env_vars' in content:
            analysis['required_changes'].append('Update test fixtures')
        
        # 檢查是否需要新的 fixtures
        if 'USE_DATABASE' in content:
            analysis['required_changes'].append('Add database test fixtures')
        
        return analysis
    
    def scan_all_tests(self):
        """掃描所有測試文件"""
        test_dir = Path('tests')
        test_files = list(test_dir.rglob('*.py'))
        
        for test_file in test_files:
            if '__pycache__' in str(test_file):
                continue
            analysis = self.analyze_test_file(test_file)
            self.test_files.append(analysis)
    
    def generate_migration_plan(self):
        """生成測試遷移計劃"""
        plan = {
            'high_complexity': [],
            'medium_complexity': [],
            'low_complexity': [],
            'summary': {
                'total_files': len(self.test_files),
                'need_migration': 0,
                'database_ready': 0
            }
        }
        
        for test_analysis in self.test_files:
            complexity = test_analysis['migration_complexity']
            
            if complexity == 'HIGH':
                plan['high_complexity'].append(test_analysis)
            elif complexity == 'MEDIUM':
                plan['medium_complexity'].append(test_analysis)
            else:
                plan['low_complexity'].append(test_analysis)
            
            if test_analysis['json_dependencies'] or test_analysis['knowledge_imports']:
                plan['summary']['need_migration'] += 1
            
            if test_analysis['database_usage']:
                plan['summary']['database_ready'] += 1
        
        return plan
    
    def generate_report(self):
        """生成測試遷移報告"""
        self.scan_all_tests()
        plan = self.generate_migration_plan()
        
        report = f"""# 測試系統遷移計劃

## 📊 總覽
- **總測試文件**: {plan['summary']['total_files']}
- **需要遷移**: {plan['summary']['need_migration']}
- **已準備就緒**: {plan['summary']['database_ready']}
- **高複雜度**: {len(plan['high_complexity'])}
- **中複雜度**: {len(plan['medium_complexity'])}
- **低複雜度**: {len(plan['low_complexity'])}

## 🔴 高優先級遷移 (HIGH Complexity)
"""
        
        for test in plan['high_complexity']:
            report += f"\n### {test['file']}\n"
            report += f"- **複雜度**: {test['migration_complexity']}\n"
            if test['json_dependencies']:
                report += f"- **JSON 依賴**: {', '.join(test['json_dependencies'])}\n"
            if test['knowledge_imports']:
                report += f"- **Knowledge 引用**: {', '.join(test['knowledge_imports'])}\n"
            if test['required_changes']:
                report += "- **需要的變更**:\n"
                for change in test['required_changes']:
                    report += f"  - {change}\n"
        
        report += f"""

## 🟠 中優先級遷移 (MEDIUM Complexity)
"""
        
        for test in plan['medium_complexity']:
            report += f"\n### {test['file']}\n"
            report += f"- **複雜度**: {test['migration_complexity']}\n"
            if test['required_changes']:
                report += "- **需要的變更**:\n"
                for change in test['required_changes']:
                    report += f"  - {change}\n"
        
        report += """

## 🎯 測試遷移策略

### 1. 更新 conftest.py
- 添加資料庫測試 fixtures
- 移除 JSON 相關的 fixtures
- 統一測試環境配置

### 2. 分階段遷移
1. **階段 1**: 更新高複雜度測試
2. **階段 2**: 批量更新中複雜度測試
3. **階段 3**: 清理和優化

### 3. 新的測試策略
- 使用 pytest-asyncio 支援異步測試
- 使用 pytest-mock 替代 JSON 文件模擬
- 增加資料庫事務隔離

### 4. 持續驗證
- 每次遷移後運行完整測試套件
- 監控測試覆蓋率變化
- 確保測試性能不降低
"""
        
        return report

def main():
    planner = TestMigrationPlanner()
    report = planner.generate_report()
    
    with open('analysis/test_migration_plan.md', 'w') as f:
        f.write(report)
    
    print("✅ 測試遷移計劃生成完成！")
    print("📄 報告位置: analysis/test_migration_plan.md")

if __name__ == "__main__":
    main()
EOF

chmod +x analysis/test_migration_plan.py
python3 analysis/test_migration_plan.py
```

### 4️⃣ 風險評估和緩解策略 (1 小時)

#### 風險評估矩陣
```bash
cat > analysis/risk_assessment.py << 'EOF'
#!/usr/bin/env python3
"""
風險評估和緩解策略生成器
"""

import json

class RiskAssessment:
    def __init__(self):
        self.risks = [
            {
                "id": "RISK-001",
                "name": "數據遺失風險",
                "category": "數據安全",
                "probability": "LOW",
                "impact": "HIGH",
                "severity": "HIGH",
                "description": "在遷移過程中可能丟失歷史學習數據",
                "mitigation": [
                    "完整數據備份",
                    "雙重驗證機制",
                    "階段性遷移",
                    "實時數據同步監控"
                ],
                "contingency": "立即回滾到備份版本"
            },
            {
                "id": "RISK-002", 
                "name": "業務中斷風險",
                "category": "業務連續性",
                "probability": "MEDIUM",
                "impact": "MEDIUM",
                "severity": "MEDIUM",
                "description": "遷移期間用戶無法正常使用學習功能",
                "mitigation": [
                    "滾動更新策略",
                    "功能開關控制",
                    "灰度發布",
                    "快速回滾機制"
                ],
                "contingency": "啟用維護模式，執行緊急回滾"
            },
            {
                "id": "RISK-003",
                "name": "性能回歸風險", 
                "category": "系統性能",
                "probability": "LOW",
                "impact": "MEDIUM",
                "severity": "LOW",
                "description": "資料庫查詢性能不如 JSON 文件讀取",
                "mitigation": [
                    "資料庫索引優化",
                    "查詢性能基準測試",
                    "連接池配置優化",
                    "緩存策略改進"
                ],
                "contingency": "調整資料庫配置，增加緩存層"
            },
            {
                "id": "RISK-004",
                "name": "開發環境複雜化",
                "category": "開發效率",
                "probability": "HIGH",
                "impact": "LOW", 
                "severity": "MEDIUM",
                "description": "開發者需要運行資料庫，增加環境配置複雜度",
                "mitigation": [
                    "Docker 容器化",
                    "一鍵啟動腳本",
                    "開發文檔更新",
                    "團隊培訓"
                ],
                "contingency": "提供詳細的故障排除指南"
            },
            {
                "id": "RISK-005",
                "name": "測試覆蓋不足",
                "category": "代碼質量",
                "probability": "MEDIUM",
                "impact": "HIGH",
                "severity": "HIGH",
                "description": "遷移後測試覆蓋率下降，未發現的 bug 增加",
                "mitigation": [
                    "重構測試套件",
                    "增加集成測試",
                    "自動化測試驗證",
                    "測試覆蓋率監控"
                ],
                "contingency": "暫停發布，補充測試用例"
            }
        ]
    
    def calculate_risk_score(self, probability: str, impact: str) -> int:
        """計算風險分數"""
        prob_score = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}[probability]
        impact_score = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}[impact]
        return prob_score * impact_score
    
    def generate_risk_matrix(self):
        """生成風險矩陣"""
        matrix = {
            "HIGH": [],
            "MEDIUM": [],
            "LOW": []
        }
        
        for risk in self.risks:
            severity = risk["severity"]
            matrix[severity].append(risk)
        
        return matrix
    
    def generate_mitigation_plan(self):
        """生成緩解計劃"""
        matrix = self.generate_risk_matrix()
        
        plan = f"""# 風險評估與緩解計劃

## 🎯 風險總覽

### 風險分布
- **高風險項目**: {len(matrix['HIGH'])}
- **中風險項目**: {len(matrix['MEDIUM'])}
- **低風險項目**: {len(matrix['LOW'])}

## 🔴 高風險項目 (立即處理)
"""
        
        for risk in matrix['HIGH']:
            plan += f"""
### {risk['id']}: {risk['name']}
- **類別**: {risk['category']}
- **發生概率**: {risk['probability']}
- **影響程度**: {risk['impact']}
- **描述**: {risk['description']}

**緩解措施**:
"""
            for mitigation in risk['mitigation']:
                plan += f"- {mitigation}\n"
            
            plan += f"\n**應急計劃**: {risk['contingency']}\n"
        
        plan += f"""

## 🟠 中風險項目 (重點關注)
"""
        
        for risk in matrix['MEDIUM']:
            plan += f"""
### {risk['id']}: {risk['name']}
- **類別**: {risk['category']}
- **描述**: {risk['description']}
- **關鍵緩解措施**: {risk['mitigation'][0]}
"""
        
        plan += """

## 🟡 低風險項目 (監控即可)
"""
        
        for risk in matrix['LOW']:
            plan += f"- **{risk['id']}**: {risk['name']} - {risk['mitigation'][0]}\n"
        
        plan += """

## 📋 風險監控檢查清單

### 遷移前檢查
- [ ] 完整數據備份已創建並驗證
- [ ] 回滾腳本已測試
- [ ] 團隊已接受培訓
- [ ] 監控系統已就緒

### 遷移過程監控
- [ ] 實時錯誤率監控 (<1%)
- [ ] 響應時間監控 (<200ms)
- [ ] 數據完整性檢查 (每小時)
- [ ] 用戶反馈監控

### 遷移後驗證
- [ ] 功能測試通過率 >99%
- [ ] 性能基準測試通過
- [ ] 數據一致性驗證
- [ ] 用戶驗收測試通過

## 🚨 緊急響應程序

### 觸發條件
1. 錯誤率 >5%
2. 響應時間 >500ms
3. 數據不一致
4. 用戶無法訪問

### 響應步驟
1. **立即**: 啟動緊急會議
2. **5分鐘內**: 評估問題嚴重性
3. **10分鐘內**: 決定是否回滾
4. **15分鐘內**: 執行回滾或修復
5. **事後**: 進行事後分析和改進
"""
        
        return plan

def main():
    assessment = RiskAssessment()
    plan = assessment.generate_mitigation_plan()
    
    with open('analysis/risk_assessment_and_mitigation.md', 'w') as f:
        f.write(plan)
    
    # 保存結構化風險數據
    with open('analysis/risk_data.json', 'w') as f:
        json.dump(assessment.risks, f, indent=2)
    
    print("✅ 風險評估完成！")
    print("📄 報告: analysis/risk_assessment_and_mitigation.md")
    print("📊 數據: analysis/risk_data.json")

if __name__ == "__main__":
    main()
EOF

chmod +x analysis/risk_assessment.py
python3 analysis/risk_assessment.py
```

## 🔧 執行驗證

### 分析結果驗證
```bash
# 檢查所有分析文件是否生成
echo "=== Analysis Files Generated ===" 
ls -la analysis/

# 驗證分析結果的完整性
echo "=== Dependency Analysis Validation ==="
if [[ -f "analysis/detailed_dependency_analysis.json" ]]; then
    python3 -c "
import json
with open('analysis/detailed_dependency_analysis.json') as f:
    data = json.load(f)
print(f'✅ JSON 依賴分析: {data[\"summary\"][\"json_related_files\"]} 個相關文件')
print(f'✅ 高風險文件: {data[\"summary\"][\"high_risk_files\"]} 個')
"
else
    echo "❌ 依賴分析文件缺失"
fi

# 驗證業務影響分析
if [[ -f "analysis/business_impact_analysis.md" ]]; then
    echo "✅ 業務影響分析完成"
    grep -c "風險等級" analysis/business_impact_analysis.md
else
    echo "❌ 業務影響分析缺失"
fi

# 驗證測試遷移計劃
if [[ -f "analysis/test_migration_plan.md" ]]; then
    echo "✅ 測試遷移計劃完成"
    grep -c "複雜度" analysis/test_migration_plan.md
else
    echo "❌ 測試遷移計劃缺失"
fi

# 驗證風險評估
if [[ -f "analysis/risk_assessment_and_mitigation.md" ]]; then
    echo "✅ 風險評估完成"
    grep -c "RISK-" analysis/risk_assessment_and_mitigation.md
else
    echo "❌ 風險評估缺失"
fi
```

### 生成最終摘要報告
```bash
cat > analysis/FINAL_ANALYSIS_SUMMARY.md << 'EOF'
# 純 Database 系統重構 - 詳細依賴分析最終報告

## 📊 執行摘要

**分析完成時間**: $(date)
**分析範圍**: 整個 Linker 專案代碼庫
**分析深度**: 代碼級別依賴 + 業務流程 + 風險評估

## 🔍 關鍵發現

### 技術發現
1. **JSON 依賴文件**: 已識別所有含 JSON 邏輯的文件
2. **風險等級分布**: 高/中/低風險文件分類完成
3. **調用鏈分析**: 完整的函數調用關係圖
4. **測試依賴**: 測試系統遷移計劃已制定

### 業務影響
1. **核心流程**: 所有關鍵業務流程都有資料庫替代方案
2. **API 端點**: 受影響的端點已標記和分類
3. **數據流向**: 完整的數據流轉換計劃
4. **用戶體驗**: 對終端用戶透明的遷移策略

### 風險控制
1. **數據安全**: 多層備份和驗證機制
2. **業務連續性**: 漸進式遷移和快速回滾
3. **質量保證**: 全面的測試覆蓋和監控
4. **團隊準備**: 完整的培訓和文檔

## 📋 後續行動計劃

### 立即行動 (TASK-30C)
- [ ] 基於分析結果配置開發環境
- [ ] 創建開發工具和腳本
- [ ] 準備團隊培訓材料

### 第一階段實施 (TASK-30D~H)
- [ ] 按風險等級順序移除 JSON 依賴
- [ ] 實施漸進式切換策略
- [ ] 持續監控和驗證

## 🎯 成功指標

- **代碼質量**: 無 JSON 引用，Linting 通過
- **測試覆蓋**: 維持 >90% 覆蓋率
- **性能指標**: 響應時間不降低
- **數據完整性**: 100% 數據一致性
- **用戶滿意度**: 無功能回歸

---

**✅ 分析階段完成**: 所有技術和業務分析已完成，可以進入實施階段。
EOF
```

## 📝 執行筆記

### 完成檢查清單
- [ ] 完整代碼掃描和依賴發現
- [ ] 深度依賴分析腳本執行
- [ ] 業務流程影響評估
- [ ] API 端點影響分析
- [ ] 測試系統遷移計劃
- [ ] 風險評估矩陣完成
- [ ] 緩解策略制定
- [ ] 最終摘要報告生成

### 重要輸出文件
- `analysis/detailed_dependency_analysis.json` - 結構化依賴數據
- `analysis/dependency_analysis_summary.md` - 依賴分析摘要
- `analysis/business_impact_analysis.md` - 業務影響評估
- `analysis/test_migration_plan.md` - 測試遷移計劃
- `analysis/risk_assessment_and_mitigation.md` - 風險評估和緩解
- `analysis/FINAL_ANALYSIS_SUMMARY.md` - 最終摘要報告

### 分析品質指標
- **覆蓋完整性**: 100% 代碼文件掃描
- **風險識別**: 5個主要風險類別
- **業務流程**: 6個核心業務流程分析
- **技術深度**: 函數級別的調用鏈分析

## 🔍 審查意見 (For Reviewer)

_(留空，供 reviewer 填寫)_

---

**✅ 任務完成標準**: 所有分析腳本執行成功，生成完整的技術和業務分析報告，風險評估和緩解計劃制定完成，為後續實施提供詳細的技術路線圖。