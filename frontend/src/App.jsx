import React, { useState, useEffect } from 'react';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

const App = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [isLoginView, setIsLoginView] = useState(true);
    const [message, setMessage] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [token, setToken] = useState(null);
    const [errors, setErrors] = useState({});

    // Load token from localStorage on component mount
    useEffect(() => {
        const savedToken = localStorage.getItem('authToken');
        if (savedToken) {
            setToken(savedToken);
        }
    }, []);

    // Save token to localStorage whenever it changes
    useEffect(() => {
        if (token) {
            localStorage.setItem('authToken', token);
        } else {
            localStorage.removeItem('authToken');
        }
    }, [token]);

    const validateForm = () => {
        const newErrors = {};

        // Email validation
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!email) {
            newErrors.email = 'Email is required';
        } else if (!emailRegex.test(email)) {
            newErrors.email = 'Please enter a valid email address';
        }

        // Password validation
        if (!password) {
            newErrors.password = 'Password is required';
        } else if (password.length < 6) {
            newErrors.password = 'Password must be at least 6 characters';
        } else if (!isLoginView && password.length < 8) {
            newErrors.password = 'Password must be at least 8 characters for registration';
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleAuth = async (e) => {
        e.preventDefault();
        setMessage('');
        setErrors({});

        if (!validateForm()) {
            return;
        }

        setIsLoading(true);

        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/auth/${isLoginView ? 'login' : 'register'}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password }),
            });

            const data = await response.json();

            if (response.ok) {
                if (isLoginView) {
                    setToken(data.access_token);
                    setMessage('Login successful! Welcome.');
                } else {
                    setMessage('Registration successful! Please login.');
                    setIsLoginView(true);
                    // Clear form after successful registration
                    setEmail('');
                    setPassword('');
                }
            } else {
                const errorMessage = data.detail || 
                    (response.status === 401 ? 'Invalid credentials' : 
                     response.status === 409 ? 'User already exists' : 
                     'An error occurred');
                setMessage(`Error: ${errorMessage}`);
            }
        } catch (error) {
            setMessage('Network error. Please check your connection and try again.');
            console.error('Fetch Error:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleLogout = () => {
        setToken(null);
        setEmail('');
        setPassword('');
        setMessage('You have been logged out.');
    };

    const switchView = () => {
        setIsLoginView(!isLoginView);
        setMessage('');
        setErrors({});
        // Clear password when switching views
        setPassword('');
    };

    // If user is authenticated, show dashboard
    if (token) {
        return (
            <div className="min-h-screen bg-gray-100 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
                <div className="sm:mx-auto sm:w-full sm:max-w-md">
                    <div className="bg-white py-8 px-4 shadow-xl sm:rounded-lg sm:px-10 border border-gray-200 text-center">
                        <h2 className="text-2xl font-bold text-gray-900 mb-4">
                            Welcome to DocuSage!
                        </h2>
                        <p className="text-gray-600 mb-6">
                            You are successfully authenticated.
                        </p>
                        <button
                            onClick={handleLogout}
                            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                        >
                            Logout
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    // Authentication form
    return (
        <div className="min-h-screen bg-gray-100 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
            <div className="sm:mx-auto sm:w-full sm:max-w-md">
                <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
                    DocuSage Auth
                </h2>
            </div>

            <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
                <div className="bg-white py-8 px-4 shadow-xl sm:rounded-lg sm:px-10 border border-gray-200">
                    <h3 className="text-center text-2xl font-bold mb-6 text-gray-800">
                        {isLoginView ? 'Sign In to Your Account' : 'Create a New Account'}
                    </h3>

                    <form onSubmit={handleAuth} className="space-y-6">
                        <div>
                            <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                                Email address
                            </label>
                            <div className="mt-1">
                                <input
                                    id="email"
                                    name="email"
                                    type="email"
                                    required
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className={`appearance-none block w-full px-3 py-2 border rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm ${
                                        errors.email ? 'border-red-500' : 'border-gray-300'
                                    }`}
                                    placeholder="you@example.com"
                                />
                                {errors.email && (
                                    <p className="mt-1 text-sm text-red-600">{errors.email}</p>
                                )}
                            </div>
                        </div>

                        <div>
                            <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                                Password
                            </label>
                            <div className="mt-1">
                                <input
                                    id="password"
                                    name="password"
                                    type="password"
                                    required
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className={`appearance-none block w-full px-3 py-2 border rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm ${
                                        errors.password ? 'border-red-500' : 'border-gray-300'
                                    }`}
                                    placeholder="••••••••"
                                    minLength={isLoginView ? 6 : 8}
                                />
                                {errors.password && (
                                    <p className="mt-1 text-sm text-red-600">{errors.password}</p>
                                )}
                            </div>
                        </div>

                        <div className="flex items-center justify-between">
                            <div className="text-sm">
                                <button
                                    type="button"
                                    onClick={switchView}
                                    className="font-medium text-indigo-600 hover:text-indigo-500 focus:outline-none"
                                >
                                    {isLoginView ? 'Need to register?' : 'Already have an account?'}
                                </button>
                            </div>
                        </div>

                        <div>
                            <button
                                type="submit"
                                disabled={isLoading}
                                className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-indigo-400 disabled:cursor-not-allowed transition"
                            >
                                {isLoading
                                    ? (isLoginView ? 'Logging In...' : 'Registering...')
                                    : (isLoginView ? 'Sign In' : 'Register')}
                            </button>
                        </div>
                    </form>

                    {message && (
                        <div className={`mt-4 p-3 rounded-lg text-sm font-medium ${
                            message.startsWith('Error') ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
                        }`}>
                            {message}
                        </div>
                    )}
                </div>

                <p className="mt-6 text-center text-sm text-gray-600">
                    Backend Status: <span className="font-semibold text-indigo-600">{API_BASE_URL}</span>
                </p>
            </div>
        </div>
    );
};

export default App;
