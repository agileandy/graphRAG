import json
import os

from neo4j import GraphDatabase, exceptions

# Adjust the path to config.json based on the script's location
CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "config", "database_config.json"
)


def load_neo4j_config():
    """Loads Neo4j configuration from the config file."""
    try:
        with open(CONFIG_PATH) as f:
            config = json.load(f)
        return config.get("neo4j")
    except FileNotFoundError:
        print(f"Error: Configuration file not found at {CONFIG_PATH}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {CONFIG_PATH}")
        return None


def check_constraints(driver) -> None:
    """Checks for the existence of specific constraints and reports their status."""
    expected_constraints = {
        "concept_name_unique": "CONSTRAINT ON ( concept:Concept ) ASSERT concept.name IS UNIQUE",
        "document_id_unique": "CONSTRAINT ON ( document:Document ) ASSERT document.id IS UNIQUE",
    }
    # Normalize expected constraint descriptions for comparison
    # (e.g. remove extra spaces, handle slight variations in Neo4j output)
    # For simplicity, we'll do a basic check here. More robust parsing might be needed
    # if Neo4j's SHOW CONSTRAINTS output varies significantly.

    present_constraints = {}
    try:
        with driver.session() as session:
            print("\nChecking for schema constraints...")
            results = session.run("SHOW CONSTRAINTS")
            for record in results:
                # record["description"] is how it's typically named, but can vary.
                # record["name"] is usually the constraint name if explicitly set.
                # We'll check description for the pattern.
                description = record.get("description", "")
                name = record.get("name", "")  # Neo4j 5.x uses 'name'

                # Try to match based on known patterns if name is not directly matched
                if (
                    "Concept" in description
                    and "name" in description
                    and "UNIQUE" in description
                ):
                    present_constraints["concept_name_unique"] = description
                elif (
                    "Document" in description
                    and "id" in description
                    and "UNIQUE" in description
                ):
                    present_constraints["document_id_unique"] = description
                elif name in expected_constraints:  # If name matches one of our keys
                    present_constraints[name] = description

            for key, desc_pattern in expected_constraints.items():
                # A more robust check would involve parsing `desc_pattern` and `present_constraints` values
                if key in present_constraints:
                    print(
                        f"  [PRESENT] Constraint for '{key}' found: {present_constraints[key]}"
                    )
                else:
                    # Fallback to check if any description contains the core elements
                    found_by_desc = False
                    for pc_desc in present_constraints.values():
                        if (
                            "Concept" in pc_desc
                            and "name" in pc_desc
                            and "UNIQUE" in pc_desc
                            and key == "concept_name_unique"
                        ) or (
                            "Document" in pc_desc
                            and "id" in pc_desc
                            and "UNIQUE" in pc_desc
                            and key == "document_id_unique"
                        ):
                            print(
                                f"  [PRESENT] Constraint for '{key}' found (matched by description): {pc_desc}"
                            )
                            found_by_desc = True
                            break
                    if not found_by_desc:
                        print(
                            f"  [MISSING] Constraint for '{key}' (expected pattern: {desc_pattern})"
                        )

    except exceptions.Neo4jError as e:
        print(f"Error checking constraints: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while checking constraints: {e}")


def main() -> None:
    """Main function to verify Neo4j connection and schema."""
    neo4j_config = load_neo4j_config()
    if not neo4j_config:
        return

    uri = neo4j_config.get("uri")
    username = neo4j_config.get("username")
    password = neo4j_config.get("password")

    if not all([uri, username, password]):
        print("Error: Neo4j URI, username, or password missing in configuration.")
        return

    driver = None
    try:
        driver = GraphDatabase.driver(uri, auth=(username, password))
        driver.verify_connectivity()
        print("Successfully connected to Neo4j.")

        # Check for constraints
        check_constraints(driver)

        # Placeholder for checking indexes if needed in the future
        # print("\nChecking for schema indexes (not implemented in this script)...")
        # Example: session.run("SHOW INDEXES") and parse results

    except exceptions.AuthError:
        print(
            f"Error: Neo4j authentication failed for user '{username}'. Check credentials."
        )
    except exceptions.ServiceUnavailable:
        print(
            f"Error: Could not connect to Neo4j at {uri}. Ensure the server is running."
        )
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if driver:
            driver.close()
            print("\nNeo4j connection closed.")


if __name__ == "__main__":
    main()
