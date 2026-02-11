import { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
} from 'react-native';
import { Link, router } from 'expo-router';
import { useAuthStore } from '@/store/auth';

export default function LoginScreen() {
  const { login, cachedPhoneNumber } = useAuthStore();
  const [phoneNumber, setPhoneNumber] = useState('+254');
  const [pin, setPin] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPhoneField, setShowPhoneField] = useState(true);

  useEffect(() => {
    if (cachedPhoneNumber) {
      setPhoneNumber(cachedPhoneNumber);
      setShowPhoneField(false);
    }
  }, [cachedPhoneNumber]);

  const handleLogin = async () => {
    if (!phoneNumber) {
      setError('Please enter your phone number');
      return;
    }

    if (pin.length !== 4 || !/^\d{4}$/.test(pin)) {
      setError('PIN must be exactly 4 digits');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await login(phoneNumber, pin);
      router.replace('/(tabs)/home');
    } catch (err) {
      setError('Invalid phone number or PIN');
    } finally {
      setLoading(false);
    }
  };

  const handleChangePhone = () => {
    setShowPhoneField(true);
    setPhoneNumber('+254');
    setPin('');
    setError('');
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      testID="login-screen"
    >
      <View style={styles.content} testID="login-content">
        <Text style={styles.title} testID="login-title">AgriScheme Pro</Text>
        <Text style={styles.subtitle} testID="login-subtitle">Farm Management System</Text>

        {error ? (
          <Text style={styles.error} testID="login-error">{error}</Text>
        ) : null}

        {/* Returning user: show cached phone and "Not you?" link */}
        {!showPhoneField && cachedPhoneNumber ? (
          <View style={styles.welcomeSection}>
            <Text style={styles.welcomeBack}>Welcome back</Text>
            <Text style={styles.phoneDisplay}>{cachedPhoneNumber}</Text>
            <TouchableOpacity onPress={handleChangePhone} testID="login-change-phone">
              <Text style={styles.changePhone}>Not you? Change number</Text>
            </TouchableOpacity>
          </View>
        ) : null}

        {/* Phone input: shown for new users or when "change number" is tapped */}
        {showPhoneField ? (
          <TextInput
            style={styles.input}
            placeholder="Phone Number (+254...)"
            value={phoneNumber}
            onChangeText={setPhoneNumber}
            keyboardType="phone-pad"
            testID="login-phone-input"
            accessibilityLabel="Phone number input"
          />
        ) : null}

        {/* PIN input: always shown */}
        <TextInput
          style={styles.input}
          placeholder="4-Digit PIN"
          value={pin}
          onChangeText={(text) => setPin(text.replace(/[^0-9]/g, ''))}
          secureTextEntry
          maxLength={4}
          keyboardType="number-pad"
          testID="login-pin-input"
          accessibilityLabel="PIN input"
        />

        <TouchableOpacity
          style={styles.button}
          onPress={handleLogin}
          disabled={loading}
          testID="login-submit-button"
        >
          {loading ? (
            <ActivityIndicator color="#fff" testID="login-loading-indicator" />
          ) : (
            <Text style={styles.buttonText}>Login</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity testID="login-forgot-pin-link">
          <Text style={styles.link}>Forgot PIN?</Text>
        </TouchableOpacity>

        <View style={styles.registerContainer} testID="login-register-container">
          <Text style={styles.registerText}>Don't have an account? </Text>
          <Link href="/(auth)/register" asChild>
            <TouchableOpacity testID="login-register-link">
              <Text style={styles.registerLink}>Register</Text>
            </TouchableOpacity>
          </Link>
        </View>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    padding: 24,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#1B5E20',
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 32,
  },
  error: {
    color: '#D32F2F',
    textAlign: 'center',
    marginBottom: 16,
  },
  welcomeSection: {
    marginBottom: 24,
    alignItems: 'center',
  },
  welcomeBack: {
    fontSize: 18,
    color: '#333',
    marginBottom: 4,
  },
  phoneDisplay: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#1B5E20',
    marginBottom: 8,
  },
  changePhone: {
    color: '#1B5E20',
    textDecorationLine: 'underline',
    fontSize: 14,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 16,
    marginBottom: 16,
    fontSize: 16,
  },
  button: {
    backgroundColor: '#1B5E20',
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
    marginBottom: 16,
  },
  buttonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  link: {
    color: '#1B5E20',
    textAlign: 'center',
    marginBottom: 24,
  },
  registerContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
  },
  registerText: {
    color: '#666',
  },
  registerLink: {
    color: '#1B5E20',
    fontWeight: '600',
  },
});
