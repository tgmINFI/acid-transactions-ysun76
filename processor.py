import sqlite3

class ShipmentProcessor:
    def __init__(self, db_path):
        self.db_path = db_path

    def process_shipment(self, item_id, quantity, log_callback):
        """
        Verarbeitet den Versand von Materialien aus dem Inventar.
        Implementiert ACID-Transaktionslogik, um Atomarität zu gewährleisten.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # START DER TRANSAKTION
        log_callback(f"--- STARTING TRANSACTION: Move {quantity} of Item {item_id} ---")
        
        try:
            # Schritt 1: Inventar aktualisieren
            # SQLite wirft einen Fehler, wenn stock_qty < 0 (CHECK constraint).
            cursor.execute(
                "UPDATE inventory SET stock_qty = stock_qty - ? WHERE id = ?",
                (quantity, item_id)
            )
            
            if cursor.rowcount == 0:
                raise ValueError(f"Artikel mit ID {item_id} nicht gefunden.")
            
            log_callback(">> STEP 1 SUCCESS: Inventory updated.")

            # Schritt 2: Versandprotokoll (Log) erstellen
            cursor.execute(
                "INSERT INTO shipment_log (item_id, quantity) VALUES (?, ?)",
                (item_id, quantity)
            )
            log_callback(">> STEP 2 SUCCESS: Shipment Logged.")

            # COMMIT: Nur speichern, wenn BEIDE Schritte erfolgreich waren
            conn.commit()
            log_callback("--- TRANSACTION COMMITTED ---")
            return True

        except Exception as e:
            # ROLLBACK: Macht alle Änderungen rückgängig
            conn.rollback()
            log_callback(f">> STEP 1 FAILED: {str(e)}")
            log_callback(">> STEP 2 SKIPPED: Rolling back transaction.")
            log_callback("--- TRANSACTION ROLLED BACK ---")
            return False
        
        finally:
            conn.close()