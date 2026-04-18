#!/bin/bash
declare -A test_map
test_map["../sdk/cpp"]="run_test_vines_cpp.sh"
test_map["../sdk/go/scykernel"]="run_test_vines_go.sh"
test_map["../sdk/java"]="run_test_vines_java.sh"
test_map["../sdk/javascript"]="run_test_vines_js.sh"
test_map["../sdk/kotlin"]="run_test_vines_kotlin.sh"
test_map["../sdk/php"]="run_test_vines_php.sh"
test_map["../sdk/python"]="run_test_vines_python.sh"
test_map["../sdk/react-native"]="run_test_vines_rn.sh"
test_map["../sdk/rust"]="run_test_vines_rust.sh"
test_map["../sdk/swift"]="run_test_vines_swift.sh"
for dir in "${!test_map[@]}"; do
    script="${test_map[$dir]}"
    if [ -d "$dir" ]; then
        echo "🚀 Entering $dir..."
        cd "$dir" || continue
        if [ -f "$script" ]; then
            chmod +x "$script"
            ./"$script"
            echo "✅ $dir complete."
        else
            echo "❌ Error: $script not found in $dir"
        fi
        cd - > /dev/null
    else
        echo "⚠️ Directory $dir does not exist."
    fi
    echo "------------------------------------"
done
echo "🏁 All mapped tests processed."