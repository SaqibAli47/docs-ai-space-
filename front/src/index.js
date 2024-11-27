import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import reportWebVitals from './reportWebVitals';
import {
  Navigate,
  createBrowserRouter,
  RouterProvider,
} from "react-router-dom";
import { Provider } from 'react-redux';
import store from './store';

import Home from './components/home';
import Settings from './components/settings';

const PrivateRoute = (props) => {
  const { children } = props
  // get params from page url, e.g. /?token=123&name=abc&picture=xyz
  const params = new URLSearchParams(window.location.search)
  // get token from url params
  const token = params.get('token', null)
  if (token){
    // save token in local storage
    localStorage.setItem('token', token)
    localStorage.setItem('email', params.get('email'))
    localStorage.setItem('name', params.get('name'))
    localStorage.setItem('language', "de")
  }
  if (localStorage.getItem('token'))
    return <>{children}</>
  window.location.href = '/api/microsoft/login'
}

const router = createBrowserRouter([
  {
    path: "/",
    element: <PrivateRoute><Navigate to="/c/new" /></PrivateRoute>,
  },
  {
    path: "/c/:chatId",
    element: <PrivateRoute><Home /></PrivateRoute>,
  },
  {
    path: "/c/new",
    element: <PrivateRoute><Home /></PrivateRoute>,
  },
  {
    path: "/c/settings",
    element: <PrivateRoute><Settings /></PrivateRoute>,
  },
]);

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <Provider store={store}>
    <React.StrictMode>
      <RouterProvider router={router} />
    </React.StrictMode>
  </Provider>
);

reportWebVitals();
