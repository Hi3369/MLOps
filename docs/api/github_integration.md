# GitHub Integration Capability

GitHub Issue 検知・ワークフロー起動を担当する Capability。

## ツール一覧

| ツール名 | 説明 |
|---------|------|
| `detect_mlops_issue` | MLOps用Issueを検知 |
| `parse_issue_config` | Issue本文からYAML/JSON設定をパース |
| `validate_training_params` | 学習パラメータをバリデーション |
| `start_workflow` | Step Functionsワークフローを起動 |

## ツール詳細

### detect_mlops_issue

MLOps用Issueを検知する。

```python
detect_mlops_issue(
    repo_owner: str,
    repo_name: str,
    issue_number: int = None,
    labels: List[str] = None,
) -> Dict[str, Any]
```

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|---|:---:|----------|------|
| repo_owner | str | o | - | リポジトリオーナー |
| repo_name | str | o | - | リポジトリ名 |
| issue_number | int | | None | 特定Issue番号 |
| labels | List[str] | | None | フィルタ用ラベル |

---

### parse_issue_config

Issue本文からYAML/JSON設定をパースする。

```python
parse_issue_config(
    issue_body: str,
    config_format: str = "auto",
) -> Dict[str, Any]
```

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|---|:---:|----------|------|
| issue_body | str | o | - | Issue本文 |
| config_format | str | | "auto" | フォーマット（auto/yaml/json） |

---

### validate_training_params

学習パラメータをバリデーションする。

```python
validate_training_params(
    training_config: Dict[str, Any],
    strict: bool = False,
) -> Dict[str, Any]
```

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|---|:---:|----------|------|
| training_config | Dict[str, Any] | o | - | 学習設定辞書 |
| strict | bool | | False | 厳密バリデーションモード |

---

### start_workflow

Step Functionsワークフローを起動する。

```python
start_workflow(
    workflow_type: str,
    input_params: Dict[str, Any],
    execution_name: str = None,
) -> Dict[str, Any]
```

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|---|:---:|----------|------|
| workflow_type | str | o | - | ワークフロータイプ（training/inference/evaluation） |
| input_params | Dict[str, Any] | o | - | ワークフロー入力パラメータ |
| execution_name | str | | None | 実行名（自動生成可） |
