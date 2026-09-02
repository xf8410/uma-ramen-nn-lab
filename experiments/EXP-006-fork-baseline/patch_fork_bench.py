#!/usr/bin/env python3
"""EXP-006b fork 适配补丁：把 pin 43f532c 的 ramen_space_bench 移植到 fork 快照。

fork（xf8410/umaai-rs @ master，2026-08-27 快照）没有 ramen_space_bench bin——
它是 pin 43f532c 才加入的 tools/data_collection bin。本脚本在 fork checkout 上：

1. 从 lab 内嵌的 bin 源码写出 crates/umasim/tools/data_collection/ramen_space_bench.rs
2. 在 crates/umasim/Cargo.toml 注册 [[bin]] 条目

移植前提（已核对两份源码）：fork 与 pin 的 bench.rs / sampler.rs / trainer 出口
API 兼容（fork 的 trainer/mod.rs 同样导出 RecommendedRamenTrainer；bench.rs 的
run_seeded/outcome_to_row/RESULTS_HEADER 同名同构）。bin 源码仅依赖这些稳定 API +
gen1_inherit/SamplingSpace，若 fork 的 sampler 缺少 gen1 常量会编译失败——那本身
就是有价值的归因信号（fork 快照尚未引入 gen1 采样空间），失败即如实报告。
"""
from pathlib import Path
import sys

BIN_SOURCE = r"""//! 采样空间基准（移植自 pin 43f532c，EXP-006b fork 独立复测用）
use std::{collections::BTreeMap, path::PathBuf};

use anyhow::{Context, Result, bail};
use clap::Parser;
use rayon::prelude::*;
use umasim::{
    bench::{self, GameOutcome},
    gamedata::init_global_with_config,
    sampler::{DeckPlan, SamplingSpace, gen1_inherit},
    trainer::{LoggingTrainer, RandomTrainer, RecommendedRamenTrainer},
    utils::{get_workspace_root, load_game_config}
};

/// 基准参数
#[derive(Parser, Debug)]
#[command(about = "在第一代采样空间（7 马娘 × 525 卡组组合）上测策略均分")]
struct BenchArgs {
    /// 策略：`handwritten`（手写规则）/ `random`（随机基线）
    #[arg(long, default_value = "handwritten")]
    trainer: String,

    /// 每个计划跑几局
    #[arg(long, default_value_t = 8)]
    runs_per_plan: u64,

    /// 基础种子；第 i 局用 `seed + i`
    #[arg(long, default_value_t = 61444)]
    seed: u64,

    /// 只跑前 N 个计划（调试用，默认全跑）
    #[arg(long)]
    plans: Option<usize>,

    /// 把逐局结果写成 CSV
    #[arg(long)]
    csv: Option<PathBuf>
}

/// 一组分数的汇总统计
#[derive(Debug, Clone, Copy)]
struct ScoreStats {
    games: usize,
    mean: f64,
    stdev: f64,
    stderr: f64
}

impl ScoreStats {
    fn from_scores(scores: &[f64]) -> Result<Self> {
        let games = scores.len();
        if games == 0 {
            bail!("没有可汇总的局");
        }
        let mean = scores.iter().sum::<f64>() / games as f64;
        let stdev = if games < 2 {
            0.0
        } else {
            let var = scores.iter().map(|s| (s - mean).powi(2)).sum::<f64>() / (games - 1) as f64;
            var.sqrt()
        };
        Ok(Self {
            games,
            mean,
            stdev,
            stderr: if games == 0 { 0.0 } else { stdev / (games as f64).sqrt() }
        })
    }
}

/// 单个计划的全部对局结果
struct PlanResult {
    plan_index: usize,
    outcomes: Vec<GameOutcome>
}

#[derive(Clone)]
enum SelectedTrainer {
    Random,
    Handwritten
}

fn select_trainer(args: &BenchArgs) -> Result<SelectedTrainer> {
    match args.trainer.as_str() {
        "random" => Ok(SelectedTrainer::Random),
        "handwritten" => Ok(SelectedTrainer::Handwritten),
        other => bail!("未知 trainer: {other}（fork 复测仅支持 random / handwritten）")
    }
}

fn run_plan(plan: &DeckPlan, plan_index: usize, args: &BenchArgs, kind: &SelectedTrainer) -> Result<PlanResult> {
    let inherit = gen1_inherit();
    let base_seed = args.seed.wrapping_add((plan_index as u64).wrapping_mul(1_000_003));
    let mut outcomes = Vec::with_capacity(args.runs_per_plan as usize);
    for run_idx in 0..args.runs_per_plan {
        let outcome = match kind {
            SelectedTrainer::Random => {
                let t = LoggingTrainer::new(RandomTrainer, base_seed + run_idx);
                bench::run_seeded(plan.uma, &plan.deck, &inherit, base_seed, run_idx, &t)?
            }
            SelectedTrainer::Handwritten => {
                let t = LoggingTrainer::new(RecommendedRamenTrainer::new(), base_seed + run_idx);
                bench::run_seeded(plan.uma, &plan.deck, &inherit, base_seed, run_idx, &t)?
            }
        };
        outcomes.push(outcome);
    }
    Ok(PlanResult { plan_index, outcomes })
}

fn print_grouped(title: &str, groups: &BTreeMap<String, Vec<f64>>) -> Result<()> {
    println!("\n{title}");
    println!("  {:<28} {:>6} {:>10} {:>9} {:>8}", "分组", "局数", "均分", "标准差", "标准误");
    for (key, scores) in groups {
        let s = ScoreStats::from_scores(scores)?;
        println!("  {:<28} {:>6} {:>10.0} {:>9.0} {:>8.1}", key, s.games, s.mean, s.stdev, s.stderr);
    }
    Ok(())
}

fn main() -> Result<()> {
    let args = BenchArgs::parse();

    let workspace_root = get_workspace_root()?;
    std::env::set_current_dir(&workspace_root)
        .with_context(|| format!("切换到工作空间根失败: {}", workspace_root.display()))?;
    init_global_with_config(&load_game_config()?)?;
    let kind = select_trainer(&args)?;

    let space = SamplingSpace::gen1()?;
    let all_plans = space.plans();
    let plans = match args.plans {
        Some(n) => &all_plans[..n.min(all_plans.len())],
        None => all_plans
    };
    println!(
        "采样空间基准（fork 复测）：{} 个计划 × {} 局 = {} 局，策略 = {}",
        plans.len(),
        args.runs_per_plan,
        plans.len() as u64 * args.runs_per_plan,
        args.trainer.clone()
    );

    let start = std::time::Instant::now();
    let mut results: Vec<PlanResult> = plans
        .par_iter()
        .enumerate()
        .map(|(i, plan)| run_plan(plan, i, &args, &kind))
        .collect::<Result<Vec<_>>>()?;
    results.sort_by_key(|r| r.plan_index);
    let elapsed = start.elapsed().as_secs_f64();

    let mut all: Vec<f64> = Vec::new();
    let mut by_shape: BTreeMap<String, Vec<f64>> = BTreeMap::new();
    let mut by_uma: BTreeMap<String, Vec<f64>> = BTreeMap::new();
    let mut free_race_fail = 0usize;
    let mut rows: Vec<Vec<String>> = Vec::new();
    for r in &results {
        let plan = &plans[r.plan_index];
        for o in &r.outcomes {
            let score = f64::from(o.score);
            all.push(score);
            by_shape.entry(plan.shape.to_string()).or_default().push(score);
            by_uma.entry(format!("{}", plan.uma)).or_default().push(score);
            if !o.free_race_ok {
                free_race_fail += 1;
            }
            if args.csv.is_some() {
                rows.push(bench::outcome_to_row(plan.shape, o));
            }
        }
    }

    let overall = ScoreStats::from_scores(&all)?;
    print_grouped("按卡组构成", &by_shape)?;
    print_grouped("按马娘", &by_uma)?;
    println!("\n合计");
    println!("  局数        {}", overall.games);
    println!("  均分        {:.0}", overall.mean);
    println!("  标准差      {:.0}", overall.stdev);
    println!("  均值标准误  {:.1}", overall.stderr);
    println!("  自选比赛未达标  {} 局（{:.2}%）", free_race_fail, 100.0 * free_race_fail as f64 / all.len() as f64);
    println!("  耗时        {elapsed:.1} s");

    if let Some(path) = &args.csv {
        bench::write_csv(path, &bench::RESULTS_HEADER, &rows)?;
        println!("  逐局 CSV    {}", path.display());
    }
    Ok(())
}
"""

CARGO_ANCHOR = """[[bin]]
name = "ramen_player"
path = "src/bin/ramen_player.rs"
required-features = ["cli", "diag"]
"""
CARGO_ADD = CARGO_ANCHOR + """
[[bin]]
name = "ramen_space_bench"
path = "tools/data_collection/ramen_space_bench.rs"
required-features = ["cli"]
"""


def main() -> int:
    bin_path = Path("crates/umasim/tools/data_collection/ramen_space_bench.rs")
    bin_path.parent.mkdir(parents=True, exist_ok=True)
    bin_path.write_text(BIN_SOURCE, encoding="utf-8")

    cargo = Path("crates/umasim/Cargo.toml")
    text = cargo.read_text(encoding="utf-8")
    if 'name = "ramen_space_bench"' in text:
        print("PATCH SKIP: fork 已有 ramen_space_bench")
        return 0
    count = text.count(CARGO_ANCHOR)
    if count != 1:
        print(f"PATCH FAIL: Cargo.toml 锚点出现 {count} 次（应为 1）")
        return 1
    cargo.write_text(text.replace(CARGO_ANCHOR, CARGO_ADD), encoding="utf-8")
    print("PATCH OK: fork +ramen_space_bench（tools/data_collection/ + Cargo.toml [[bin]]）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
