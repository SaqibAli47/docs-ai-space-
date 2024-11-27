import { configureStore } from '@reduxjs/toolkit';
import userReducer from './slice/user';
import documentSlice from './slice/document';

export default configureStore({
  reducer: {
    user: userReducer,
    document: documentSlice,
  },
})
