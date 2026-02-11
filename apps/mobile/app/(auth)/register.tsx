import { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import { Link, router } from 'expo-router';
import { useAuthStore } from '@/store/auth';

export default function RegisterScreen() {
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    phone: '+254',
    pin: '',
    confirmPin: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { register } = useAuthStore();

  const handleRegister = async () => {
    // Validate required fields
    if (!formData.firstName.trim() || !formData.lastName.trim() || !formData.phone.trim()) {
      setError('Name and phone number are required');
      return;
    }

    // Validate Kenyan phone number format
    const phoneRegex = /^\+254[17]\d{8}$/;
    if (!phoneRegex.test(formData.phone)) {
      setError('Enter a valid phone number (e.g. +254712345678)');
      return;
    }

    if (formData.pin.length !== 4 || !/^\d{4}$/.test(formData.pin)) {
      setError('PIN must be exactly 4 digits');
      return;
    }

    if (formData.pin !== formData.confirmPin) {
      setError('PINs do not match');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await register(formData);
      router.replace('/(tabs)/home');
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      let errorMessage = 'Registration failed. Please try again.';

      if (Array.isArray(detail) && detail.length > 0) {
        const firstError = detail[0];
        const field = firstError.loc?.slice(-1)[0] || 'field';
        errorMessage = `${field}: ${firstError.msg}`;
      } else if (typeof detail === 'string') {
        errorMessage = detail;
      } else if (err?.message) {
        errorMessage = err.message;
      }

      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView testID="register-screen" contentContainerStyle={styles.scrollContent}>
        <Text style={styles.title}>Create Account</Text>
        <Text style={styles.subtitle}>Join AgriScheme Pro</Text>

        {error ? <Text style={styles.error} testID="register-error">{error}</Text> : null}

        <TextInput
          testID="firstname-input"
          style={styles.input}
          placeholder="First Name"
          value={formData.firstName}
          onChangeText={(text) => setFormData({ ...formData, firstName: text })}
          autoCapitalize="words"
        />

        <TextInput
          testID="lastname-input"
          style={styles.input}
          placeholder="Last Name"
          value={formData.lastName}
          onChangeText={(text) => setFormData({ ...formData, lastName: text })}
          autoCapitalize="words"
        />

        <TextInput
          testID="phone-input"
          style={styles.input}
          placeholder="Phone Number (+254...)"
          value={formData.phone}
          onChangeText={(text) => setFormData({ ...formData, phone: text })}
          keyboardType="phone-pad"
        />

        <TextInput
          testID="pin-input"
          style={styles.input}
          placeholder="4-Digit PIN"
          value={formData.pin}
          onChangeText={(text) => setFormData({ ...formData, pin: text.replace(/[^0-9]/g, '') })}
          secureTextEntry
          maxLength={4}
          keyboardType="number-pad"
        />

        <TextInput
          testID="confirm-pin-input"
          style={styles.input}
          placeholder="Confirm PIN"
          value={formData.confirmPin}
          onChangeText={(text) => setFormData({ ...formData, confirmPin: text.replace(/[^0-9]/g, '') })}
          secureTextEntry
          maxLength={4}
          keyboardType="number-pad"
        />

        <TouchableOpacity
          testID="register-button"
          style={styles.button}
          onPress={handleRegister}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.buttonText}>Register</Text>
          )}
        </TouchableOpacity>

        <View style={styles.loginContainer}>
          <Text style={styles.loginText}>Already have an account? </Text>
          <Link href="/(auth)/login" asChild>
            <TouchableOpacity testID="login-link">
              <Text style={styles.loginLink}>Login</Text>
            </TouchableOpacity>
          </Link>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 24,
  },
  title: {
    fontSize: 28,
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
  loginContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
  },
  loginText: {
    color: '#666',
  },
  loginLink: {
    color: '#1B5E20',
    fontWeight: '600',
  },
});
