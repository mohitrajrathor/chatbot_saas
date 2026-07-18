<template>
	<div id='home'>
		<h1 class="text-3xl font-bold underline">
			Home page
		</h1>
		<p>here is your token : {{ user.token }}</p>
		<Button @click='press' class="bg-blue-500 p-2 rounded-xl text-white">press</Button>
		<p>You pressed {{ count }} times!</p>
	</div>
</template>

<script>
import Button from 'primevue/button'
import useUserStore from '../stores/user'

export default {
	name: 'Home',

	data() {
		return {
			count: 0,
			user: useUserStore(),
		};
	},

	methods: {
		press() {
			this.count++;
		},
	},
};
</script>