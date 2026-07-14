# Fetching latest copy of common constraints from edx-lint repo
wget -O "requirements/common_constraints.txt" https://raw.githubusercontent.com/edx/edx-lint/master/edx_lint/files/common_constraints.txt || touch "requirements/common_constraints.txt"

common_constraints=()
local_constraints=()
updated_common_constraints=()

while IFS= read -r line; do
    if [ -n "$line" ] && [ "${line:0:1}" != "#" ];
    then
        # Read common constraints from common constraints file
        common_constraints+=("$line")
    fi
done < requirements/common_constraints.txt

while IFS= read -r line; do
    if [ -n "$line" ] && [ "${line:0:1}" != "#" ] && [ "${line:0:1}" != "-" ];
    then
        # Read local constraints from constraints file for comparison
        local_constraints+=("$line")
    fi
done < requirements/constraints.txt


for common in "${common_constraints[@]}"
do
    # Extract package name from constraint
    common_package=$(echo "$common" | sed 's/\([a-zA-Z0-9-]*\).*/\1/')
    found=false
    for local in "${local_constraints[@]}"
    do
        # Extract package name from constraint
        local_package=$(echo "$local" | sed 's/\([a-zA-Z0-9-]*\).*/\1/')
        if [ "$common_package" = "$local_package" ];
        then
            # Update the flag if local pin is found on same package
            found=true
            break
        fi
    done
    if [ "$found" = false ];
    then
        updated_common_constraints+=("$common")
    fi
done

# Adding filtered common constraints into a file before running pip-compile and add reference of this file in constraints file.
printf "%s\n" "${updated_common_constraints[@]}" > requirements/common_constraints.txt
echo "-c common_constraints.txt" >> requirements/constraints.txt
