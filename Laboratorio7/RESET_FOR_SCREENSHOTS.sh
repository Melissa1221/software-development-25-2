#!/bin/bash
# Script to reset all modules before taking screenshots
# Run this before you start taking screenshots for clean state

echo "🧹 Cleaning up all modules for fresh screenshots..."

BASE_DIR="/Users/melissaimannoriega/Documents/UNI/7CICLO/DS/software-development-25-2/Laboratorio7"

# Adapter
echo "Cleaning Adapter..."
cd "$BASE_DIR/Adapter"
rm -rf .terraform .terraform.lock.hcl terraform.tfstate* tfplan 2>/dev/null

# Facade
echo "Cleaning Facade..."
cd "$BASE_DIR/Facade"
rm -rf .terraform .terraform.lock.hcl terraform.tfstate* tfplan buckets/ 2>/dev/null

# Inversion_control
echo "Cleaning Inversion_control..."
cd "$BASE_DIR/Inversion_control"
rm -rf .terraform .terraform.lock.hcl terraform.tfstate* tfplan main.tf.json 2>/dev/null
rm -rf network/.terraform network/.terraform.lock.hcl network/terraform.tfstate* network/network_outputs.json 2>/dev/null

# Inyeccion_dependencias
echo "Cleaning Inyeccion_dependencias..."
cd "$BASE_DIR/Inyeccion_dependencias"
rm -rf .terraform .terraform.lock.hcl terraform.tfstate* tfplan server.tf.json 2>/dev/null
rm -rf network/.terraform network/.terraform.lock.hcl network/terraform.tfstate* network/network_metadata.json 2>/dev/null

# Mediator
echo "Cleaning Mediator..."
cd "$BASE_DIR/Mediator"
rm -rf .terraform .terraform.lock.hcl terraform.tfstate* tfplan 2>/dev/null

echo "✅ All modules cleaned! Ready for screenshots."
echo ""
echo "Now you can start taking screenshots following Screenshot_Commands.md"
