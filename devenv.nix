{ pkgs, lib, config, inputs, ... }:

{
  packages = with pkgs; [
    mypy
    candle
  ];

  languages.python = {
    enable = true;
  };
}
