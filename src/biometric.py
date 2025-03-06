from PyQt6.QtWidgets import QMessageBox
from LocalAuthentication import (LAContext, LAPolicyDeviceOwnerAuthenticationWithBiometrics,
                               LAError)
from PyQt6.QtCore import QEventLoop

class BiometricAuth:
    @staticmethod
    def authenticate(parent=None) -> bool:
        try:
            context = LAContext.alloc().init()
            error = None
            loop = QEventLoop()
            auth_success = False
            
            # Check if biometric authentication is available
            can_evaluate, error = context.canEvaluatePolicy_error_(
                LAPolicyDeviceOwnerAuthenticationWithBiometrics,
                None
            )
            
            if not can_evaluate:
                error_msg = str(error) if error else "Biometric authentication not available"
                QMessageBox.warning(parent, "Authentication Error", error_msg)
                return False
            
            # Perform biometric authentication
            reason = "Authenticate to access Finance Tracker"
            def reply(success, error):
                nonlocal auth_success
                if not success:
                    error_msg = str(error) if error else "Authentication failed"
                    QMessageBox.warning(parent, "Authentication Error", error_msg)
                    auth_success = False
                else:
                    auth_success = True
                loop.quit()

            context.evaluatePolicy_localizedReason_reply_(
                LAPolicyDeviceOwnerAuthenticationWithBiometrics,
                reason,
                reply
            )
            
            # Wait for authentication to complete
            loop.exec()
            return auth_success
            
        except Exception as e:
            QMessageBox.critical(parent, "System Error", 
                f"Authentication error: {str(e)}")
            return False