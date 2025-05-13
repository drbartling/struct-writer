use anyhow::{anyhow, ensure, Result};
use std::env;
use std::path::PathBuf;
use std::process::Command;

fn main() -> Result<()> {
    println!("cargo::rerun-if-changed=build.rs");

    let out_dir = env::var_os("OUT_DIR").ok_or_else(|| anyhow!("Unable to get `OUT_DIR`"))?;
    let out_dir = PathBuf::from(out_dir);

    let examples_dir = examples_dir()?;

    let definition_files = [examples_dir.join("structures.toml")];

    let template_files = [examples_dir.join("template_rust.toml")];

    generate_structs(
        out_dir.join("example_structs.rs"),
        &definition_files,
        &template_files,
    )?;

    Ok(())
}

fn examples_dir() -> Result<PathBuf> {
    let this_file = PathBuf::from(file!()).canonicalize()?;
    let rust_example_dir = this_file.parent().unwrap();
    let examples_dir = rust_example_dir.parent().unwrap();
    ensure!(examples_dir.is_dir());
    Ok(examples_dir.into())
}

fn generate_structs(
    out_file: PathBuf,
    input_definitions: &[PathBuf],
    template_files: &[PathBuf],
) -> Result<()> {
    let mut cmd = Command::new("struct-writer");
    cmd.arg("--output-file");
    cmd.arg(&out_file);
    cmd.arg("--language");
    cmd.arg("rust");

    input_definitions.iter().for_each(|p| {
        cmd.arg("--input-definitions");
        cmd.arg(p);
        println!("cargo::rerun-if-changed={}", p.display());
    });

    template_files.iter().for_each(|p| {
        cmd.arg("--template-files");
        cmd.arg(p);
        println!("cargo::rerun-if-changed={}", p.display());
    });

    let status = cmd.status()?;
    ensure!(status.success());

    let mut format_cmd = Command::new("rustfmt");
    cmd.arg(&out_file);
    let status = format_cmd.status()?;
    ensure!(status.success());

    Ok(())
}
