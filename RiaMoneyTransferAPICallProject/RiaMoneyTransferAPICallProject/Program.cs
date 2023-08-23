using System.Net.Http.Json;
using System.Net.Http.Headers;
using System.Text.Json;
using System.Text.Json.Serialization;
using Newtonsoft.Json;
using System.Transactions;
using System.Text;

namespace RiaMoneyTransferAPICallProject
{
    internal class Program
    {

        static void Main(string[] args)
        {


            bool hasAskedToStop = false;

            while (!hasAskedToStop)
            {
                Console.WriteLine("Please select the appropriate action");
                Console.WriteLine("1. Get all User from the API");
                Console.WriteLine("2. Add User to update the records in API");
                Console.WriteLine("3. Click anything other integer to stop the application");
                int c = Convert.ToInt32(Console.ReadLine());
                switch (c)
                {
                    case 1: GetAllUsersData(); break;
                    case 2: AddAllUsersDatatoAPI(); break;
                    default: hasAskedToStop = true; break;

                }
                Console.WriteLine();
            }

            Console.WriteLine("Application Execution Executed");

        }

        static async void GetAllUsersData()
        {
            using (HttpClient client = new HttpClient())
            {
                List<User>? users = null;
                client.BaseAddress = new Uri("https://localhost:7072");
                client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));
                HttpResponseMessage responseMessage = await client.GetAsync(client.BaseAddress + "GetAllUsers");
                if (responseMessage != null && responseMessage.IsSuccessStatusCode)
                {
                    string userString = await responseMessage.Content.ReadAsStringAsync();
                    users = JsonConvert.DeserializeObject<List<User>>(userString);
                }
                PrintAllUsers(users);

            }
        }

        static async void AddAllUsersDatatoAPI()
        {
            using (HttpClient client = new HttpClient())
            {
                List<User>? users = new();
                bool hasAskedToStop = false;
                while (!hasAskedToStop)
                {
                    Console.WriteLine("Select the appropriate option");
                    Console.WriteLine("1. Add user to list");
                    Console.WriteLine("2. Send the Post API call");

                    int choice = Convert.ToInt32(Console.ReadLine());

                    switch (choice)
                    {
                        case 1: MakeUser(ref users); break;
                        default: hasAskedToStop=true; break;
                    }
                }
                    client.BaseAddress = new Uri("https://localhost:7072");
                    client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

                    if (users != null || users.Count != 0)
                    {
                        var jsonContent = new StringContent(JsonConvert.SerializeObject(users), Encoding.UTF8, "application/json");
                        HttpResponseMessage responseMessage = await client.PostAsync(client.BaseAddress + "AddUser", jsonContent);
                        if (responseMessage != null && responseMessage.IsSuccessStatusCode)
                        {
                            string userString = await responseMessage.Content.ReadAsStringAsync();
                            users = JsonConvert.DeserializeObject<List<User>>(userString);
                        }
                        PrintAllUsers(users);
                    }
                    else {
                        Console.WriteLine("Please add user before requesting the call");
                        
                    }


                    

                
            }


        }
        static void PrintAllUsers(List<User> users)
        {
            if (users != null)
            {
                Console.WriteLine("User with all the details can be found below : ");

                for (int i = 0; i < users.Count; i++)
                {
                    Console.WriteLine($"User id: {users[i].id} , FirstName : {users[i].firstName} , LastName : {users[i].lastName} , age : {users[i].age}");

                }
            }

        }
        static void MakeUser(ref List<User> users)
        {
            Console.WriteLine("Enter the new User Id : ");
            int id =Convert.ToInt32(Console.ReadLine());
            Console.WriteLine("Enter the new User first name : ");
            string firstName = Console.ReadLine();
            Console.WriteLine("Enter the new User last name : ");
            string lastName = Console.ReadLine();
            Console.WriteLine("Enter the new User age : ");
            int age = Convert.ToInt32(Console.ReadLine());
            User user = new User()
            { 
                id = id,firstName=firstName,lastName=lastName,age=age
            };
            users.Add(user);
        }
    }
}