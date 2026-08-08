import { defineStore } from 'pinia'

const useUserStore = defineStore('user', {
    state: () => ({
        token: 'testing',
    })
})

export default useUserStore